# Big Five App — Source Analysis (pre-plan)

Date: 2026-07-11. Prepared before the `/grill-with-docs` session. Synthesizes three sources:
the IPIP-NEO-PI reference implementation, the stale `personality-test` codebase, and the
`design_handoff_bigfive_flow` wireframes (web screens 2a–2g).

## 1. Product vision (from handoff)

A web app where a user takes a Big Five (IPIP-NEO) test with Gallup-style mechanics — a soft
30-second per-item timer and a continuous slider — then gets a plain-language O·C·E·A·N report,
can download it as PDF, and can spin up a personal AI coach seeded with their results
(chat, check-ins, goals). Flow: Start (choose Quick 60 / Full 120) → timed slider questions →
scoring transition → report (variant A narrative recommended) → coach intro → coach workspace.

Target stack (decided): **React + FastAPI**, VertexAI adapter for the coach LLM (key via `.env`),
Docker Compose for local run, GitHub PR-based delivery to `pawelwyparlo/personality-test`.

## 2. IPIP-NEO methodology (reference: /Users/Montrose/IPIP-NEO-PI)

### Item bank
- **120 items** (IPIP-NEO-120), embedded in `app/views/shortipipneo.html` as form radios.
- 5 domains × 6 facets × 4 items. Facet *i* (1–30) uses items `[i, i+30, i+60, i+90]`.
- 5-point Likert: Very Inaccurate (1) → Very Accurate (5).
- **⚠ Reverse keying: 55 of 120 items are negatively keyed.** The reference implementation bakes
  the reversal into the HTML radio *values* (5→1), which is why `evaluator.py` contains no keying
  logic. Our port must carry an explicit `keyed: '+'|'-'` per item and reverse server-side
  (slider emits raw 1–5). Reversed items: Q9, Q19, Q24, Q30, Q39, Q40, Q48, Q49, Q51, Q53, Q54,
  Q60, Q62, Q67–Q70, Q73–Q75, Q78–Q81, Q83–Q85, Q88–Q90, Q92, Q94, Q96–Q111, Q113–Q116, Q118–Q120.
- **No 60-item bank or norms exist in the reference repo.** The wireframe's "Quick (60)" path has
  no methodology behind it yet — open product decision (§5).

### Scoring pipeline (`app/evaluator.py`)
1. Raw facet score = sum of its 4 items (range 4–20): `ss[i] = Q[i] + Q[i+30] + Q[i+60] + Q[i+90]`.
2. Raw domain score = sum of its 6 facets (range 24–120).
3. **Norms**: 8 tables (sex × age bands `<21, 21–40, 41–60, >60`), 66 floats each
   (domain means/SDs + 30 facet means/SDs), at `evaluator.py:70–686`.
4. T-scores: `T = 50 + 10 * (raw − mean) / sd` for domains and facets.
5. Percentiles via cubic approximation with magic constants
   `210.335958661391, 16.7379362643389, 0.405936512733332, 0.00270624341822222`:
   `P = int(C1 − C2·T + C3·T² − C4·T³)`, clipped to 1 below T=32 and 99 above T=73.
6. Level classification: low `T<45`, average `45–55`, high `T>55`.

**Consequence: scoring requires the user's age and sex. The wireframes have no demographics
step — a genuine flow gap** (§5).

### Narrative
Reference narrative is a static text bank hard-coded in `views/results.html` (Bottle template
conditionals): per domain, 3 variants (low/average/high) + 6 facet descriptions with level labels.
Thresholds T=45/55. No dynamic text. The wireframe's report (pull-quote, "Who you are" prose,
Strengths, Watch-outs) is *not* expressible from this bank alone → narrative generation is an
open decision (LLM vs text bank vs hybrid, §5).

### Verification assets
- `app/tests/common.py`: exact 120-answer reference vector.
- `app/tests/reference.dat`: sample response sets with metadata.
- Port acceptance test: replay reference answers → assert identical domain/facet percentiles vs
  reference implementation output.

### Licensing
Public domain (code); IPIP items freely usable per https://ipip.ori.org/newPermission.htm.
Credit Dr. John A. Johnson + IPIP.

## 3. Stale codebase (this repo, pre-rewrite)

Vue 3 + Vite + TS + Pinia frontend, Flask stub backend. Verdict: **full teardown is safe** —
backend routes are empty stubs, store unused, no hidden integrations. Conceptually carry over:
- **TimeBar semantics** (the one carefully-built piece): 30s duration, `requestAnimationFrame`
  loop comparing `performance.now()` deltas, emits `time-up` at expiry, parent resets elapsed to 0
  on advance. Recreate in React with identical semantics.
- Three-view flow skeleton (home → question loop → results) and per-question timer reset.
- Git: remote `origin/development` branch exists alongside `main`.

## 4. Design handoff — extraction highlights

Full verbatim copy per screen extracted (see design-analyst report; copy baseline lives in the
wireframe README + HTML). Key facts beyond the README:

- **Coach sub-views (Check-ins, Goals, My report) are nav labels only — never drawn.** Only Chat
  (2g) is designed. Sidebar has a "This week's goal" widget hinting at Goals.
- **Mobile-only reveals** (we build web-only, but these are flow states desktop lacks):
  coach *setup* screen (name your coach, multi-select focus areas: Daily check-ins / Goal setting /
  Discuss my report / Habits / Relationships; privacy note "Trained only on your results & chats"),
  and a "Skip" button on questions. Desktop 2f jumps straight to a coach pre-named "Sol".
- **Error states are not designed** (README acknowledges); retry state for failed scoring needed.
- Sample scores used throughout: O 72 · C 84 · E 38 · A 61 · N 29 (0–100 = percentile scale).
- Animations: `spin` 1s linear (spinner), `blink` 1.2–1.4s staggered (OCEAN chips, typing dots).
- Report tokens/typography are wireframe stand-ins; recommended direction: warm off-white,
  grounded green accent (#3f7d5c/#5aa17a family), humanist serif for narrative, humanist sans for UI.

## 5. Product decisions

### Decided (product owner Q&A, 2026-07-11)

1. **Quick (60) path**: source the published **IPIP-NEO-60** short form properly (items, keying,
   scoring/norms) and ship both paths. Research task on critical path; if validated norms turn out
   not to exist, revisit before build.
2. **Demographics**: collect **age + sex on the start screen** (2a or a micro-step after it),
   before the test begins.
3. **Report**: variant **2d (narrative + score bars)**. Narrative (pull-quote, "Who you are",
   strengths, watch-outs) **LLM-generated via VertexAI**, with a **deterministic text-bank
   fallback** so the report always renders without an API key.
4. **Coach v1 scope**: **Chat + "My report" tab**. Check-ins and Goals appear as disabled
   "coming soon" nav items; sidebar goal widget deferred with them.

### Resolved in grill session (2026-07-11) — see CONTEXT.md, docs/adr/, docs/PLAN.md

5. **Timer expiry**: commit slider as-is; untouched = Neutral. **No Back button** (ADR-0001).
6. **Save & exit**: exit = abandon; link relabelled "Exit test". No resumability in v1.
7. **Identity**: anonymous Profile for test+report; **Clerk** account claims Profile at coach
   creation (ADR-0002). Postgres (Compose) instead of SQLite.
8. **PDF**: server-side WeasyPrint.
9. **Coach setup**: none — default "Sol"; coach tracks latest completed run; SSE streaming chat.
10. **LLM orchestration**: thin VertexAI adapter, no LangChain/LangGraph (ADR-0003).

## 6. Environment facts

- Remote: `https://github.com/pawelwyparlo/personality-test` (public, default `main`), `gh` authed.
- Docker 28.3.3 + Compose v2.39 running locally.
- Delivery mode: self-managed feature branches → PRs → self-merge; run locally via Compose.
