# Big Five App — General Development Plan

Date: 2026-07-11. Follows `docs/ANALYSIS.md` (source analysis) and the grill session
(decisions in `CONTEXT.md` + `docs/adr/`). Delivery: feature branches → GitHub PRs to
`pawelwyparlo/personality-test`, self-reviewed and self-merged; app runs locally via Docker Compose.

## Locked decisions (summary)

| Area | Decision |
|---|---|
| Stack | React + Vite + TS frontend · FastAPI backend · Postgres (Compose) |
| Forms | Full = IPIP-NEO-120 (ported); Quick = IPIP-NEO-60 (sourcing research in flight) |
| Demographics | Age + sex collected on the start screen, before the test |
| Test mechanics | 30s soft timer (rAF, TimeBar semantics), continuous slider mapped to 1–5, keyboard 1–5; expiry commits slider as-is (untouched = Neutral); **no Back** (ADR-0001); exit = abandon ("Exit test" label) |
| Scoring | Port of reference evaluator: per-item keying (55/120 reversed), raw → T-score vs 8 age/sex norm tables → cubic percentile; golden parity tests against the reference implementation |
| Report | Variant 2d (narrative + bars); narrative via VertexAI with deterministic text-bank fallback (ADR-0003); PDF server-side (WeasyPrint) |
| Identity | Anonymous Profile for test + report; Clerk account claims Profile at Coach creation (ADR-0002) |
| Coach v1 | Chat (SSE streaming) + "My report" tab; Check-ins/Goals = disabled "coming soon"; default name "Sol", no setup step; tracks latest completed run |
| LLM | Thin `LLMClient` interface, VertexAI impl, config from `.env`; no LangChain/LangGraph (ADR-0003) |

## Architecture

```
personality-test/
├── frontend/          React 19 + Vite + TS · react-router · TanStack Query · zustand (test state)
│                      Clerk React SDK · design tokens from handoff (real type/colors, not wireframe font)
├── backend/           FastAPI · SQLAlchemy 2 + Alembic · pydantic v2 · sse-starlette
│   ├── app/scoring/   item banks (JSON data: text, domain, facet, keying), norms, evaluator, text bank
│   ├── app/report/    narrative service (LLMClient + fallback), WeasyPrint PDF
│   ├── app/coach/     coach service, SSE chat, Clerk JWT verification
│   └── tests/         golden parity tests (reference vectors from IPIP-NEO-PI/app/tests)
├── docs/              ANALYSIS.md · PLAN.md · adr/ · research/
├── CONTEXT.md         glossary (grill session)
└── docker-compose.yml db (postgres:16) · backend (uvicorn --reload) · frontend (vite dev)
```

API (REST, `/api/v1`): `POST /profiles` · `GET /forms/{form}/items` · `POST /test-runs` ·
`POST /test-runs/{id}/answers` · `POST /test-runs/{id}/complete` (returns Scores + narrative;
2c screen covers this call) · `GET /reports/{run}` + `/pdf` · `POST /coach` (auth) ·
`GET/POST /coach/messages` (POST streams SSE).

`.env` (gitignored, `.env.example` committed): `GOOGLE_CLOUD_PROJECT`, `GOOGLE_APPLICATION_CREDENTIALS`
(or `VERTEX_API_KEY`), `CLERK_SECRET_KEY`, `VITE_CLERK_PUBLISHABLE_KEY`, `DATABASE_URL`.
App degrades gracefully without keys: report falls back to text bank; coach gate shows setup notice.

## PR sequence (vertical slices, each merged before the next starts)

1. **PR1 — Teardown & scaffold**: remove Vue/Flask, monorepo layout above, app shells (React router
   + theme tokens, FastAPI health + DB + Alembic), docker-compose, `.env.example`, README, docs
   (ANALYSIS/PLAN/CONTEXT/ADRs). *Gate: `docker compose up` serves both, health checks green.*
2. **PR2 — Scoring engine**: 120-item bank extraction (text/domain/facet/keying), 8 norm tables,
   evaluator port, text bank port, `/forms` + scoring services. *Gate: golden parity test — reference
   answer vectors produce identical domain+facet percentiles to the reference implementation.*
3. **PR3 — Test-taking flow**: screens 2a (with demographics + form choice), 2b (slider + TimeBar +
   keyboard + expiry semantics), 2c (scoring transition + error/retry state); Profile issuance;
   test-run API; abandonment. *Gate: full anonymous 120-item run end-to-end in the browser.*
4. **PR4 — Report**: 2d layout, narrative via VertexAI + fallback, score bars, strengths/watch-outs,
   PDF endpoint + download. *Gate: report renders with and without an LLM key; PDF downloads.*
5. **PR5 — Coach**: Clerk integration + account gate, 2f intro, 2g workspace (SSE chat, typing
   indicator, "knows: O·C·E·A·N" header, My report tab, coming-soon nav). *Gate: chat streams with
   trait-aware system prompt; retake updates coach context.*
6. **PR6 — Quick form + polish**: IPIP-NEO-60 (Maples-Keller 2019) — items sourced from
   ipip.ori.org, domain-level age×sex norms **derived** from Johnson's OSF IPIP-NEO-120 dataset
   (no published norms exist), Quick report **domain-only** (2-item facets not shipped); see
   ADR-0004. Playwright happy-path e2e, empty/error states, final copy pass. Descope to Full-only
   if trustworthy derived norms prove infeasible.

## Execution model

Orchestrator (this session) plans, reviews, merges. Opus `implementer` agents build each PR in an
isolated worktree; `reviewer`/`verifier` agents check before merge (parity tests are the hard gate
for PR2). Every UI-bearing PR is additionally verified pre-merge by a lightweight Sonnet agent that
drives the running app via Playwright (navigates the real screens, asserts the happy path) — a
runtime check on top of the unit/parity gates. The IPIP-NEO-60 research report
(`docs/research/ipip-neo-60.md`, in flight) gates PR6's scope only — PRs 1–5 are unblocked.

### Test mode

When `VITE_TEST_MODE=true` (off by default; declared in `.env.example`) the UI exposes hidden
testing controls so a full run can be driven fast without hand-answering 120 items:

- On the question screen, an **"Autofill & finish"** button fills every remaining Item with a
  random 1–5 Answer **through the normal answer path** (same commit semantics as the slider), then
  jumps straight to scoring → report.
- On the start screen, a demographics **prefill** (age + sex) so the run can begin in one click.

These controls land in PR3 and are the hook the Playwright verifier uses to reach the report screen
deterministically. With the flag unset they are absent from the DOM.

## Risks

- **IPIP-NEO-60 sourcing** — if no freely retrievable validated item list + norms: descope Quick to
  "coming soon" (start screen card disabled) and ship Full-only. Decision point at PR6.
- **WeasyPrint system deps** (pango/cairo) — handled in the backend Docker image, not host installs.
- **Clerk locally** — solved by design: Clerk **Development instances** (the dashboard default,
  free) exist exactly for this. `pk_test_`/`sk_test_` keys work on any `localhost` port with no
  domain config; sign-in UI is served via the instance's `<slug>.accounts.dev` Account Portal;
  Google social login works out of the box on **shared dev credentials** (no OAuth app setup).
  Dev-instance caveats: 100-user cap, "Development" banner, dev-only `__clerk_db_jwt` session
  handoff — all irrelevant for local use. FastAPI verifies session JWTs with the official
  `clerk-backend-api` Python SDK (`authenticate_request`, networkless via JWKS). One-time manual
  step for the user: create the free Clerk app in the dashboard and paste the two keys into `.env`.
  Everything before the coach gate works with no keys at all.
