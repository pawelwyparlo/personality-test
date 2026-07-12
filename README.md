# Big Five

A web app where a person takes an IPIP-NEO Big Five personality test with
Gallup-style mechanics (a soft per-item timer and a continuous slider), receives
a plain-language O·C·E·A·N report they can download as a PDF, and can talk to an
AI coach seeded with their results.

The stack is a React + Vite + TypeScript frontend, a FastAPI backend, and
Postgres — all orchestrated with Docker Compose for local development.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (with Compose v2)

That is the only requirement — Node, Python, and Postgres all run inside
containers.

## Run it

```bash
cp .env.example .env          # sane defaults; no keys needed to start
docker compose up --build
```

Then open:

| Service        | URL                                   |
| -------------- | ------------------------------------- |
| Frontend       | http://localhost:5173                 |
| Backend health | http://localhost:8000/api/v1/health   |
| API docs       | http://localhost:8000/docs            |

The health endpoint returns `{"status":"ok","db":true}` once Postgres is up and
migrations have applied. The app runs with **no** LLM or Clerk keys set — the
report falls back to a deterministic text bank and the coach shows a setup
notice. Add keys to `.env` (see the comments there) to enable those features.

Stop everything with `docker compose down` (add `-v` to also drop the database
volume).

> The default `.env.example` remaps host ports (DB `55432`, backend `18000`,
> frontend `15173`) to avoid clashing with anything already bound on the usual
> `5432`/`8000`/`5173`. The table above lists the in-container defaults; use
> whatever ports your `.env` sets.

## The two forms

A Test Run picks one of two published lengths on the start screen:

- **Full** — IPIP-NEO-120 (Johnson, 2014). Five domain scores **plus** all 30
  facet scores. The default (recommended) length.
- **Quick** — IPIP-NEO-60 (Maples-Keller et al., 2019), ~10 min. **Domain-only**
  by design: with 2 items per facet, facet scores are too noisy to report, so the
  Quick report ships the five domain percentiles only. Its age×sex domain norms
  are derived from Johnson's public 619k IPIP-NEO-120 dataset. See
  [ADR-0004](docs/adr/0004-quick-form-ipip-neo-60-derived-norms.md) and
  [docs/research/ipip-neo-60.md](docs/research/ipip-neo-60.md).

## Optional keys — LLM narrative and the coach

Everything up to the coach account gate works with no keys at all. Two features
light up when configured; add the values to `.env` and **restart** the affected
service (`docker compose restart backend` / `frontend`) — no rebuild needed.

### VertexAI (report narrative + coach chat)

Without a key the report uses the deterministic text bank (`source: "textbank"`)
and the coach gate shows a setup notice. To enable the LLM path, set in `.env`:

- `GOOGLE_CLOUD_PROJECT` — your GCP project id.
- Credentials, either `GOOGLE_APPLICATION_CREDENTIALS` (path to a service-account
  JSON, mounted into the backend container) **or** `VERTEX_API_KEY`.
- `VERTEX_MODEL` — optional model override (defaults are set in the backend).

### Clerk (coach account, ADR-0002)

The coach is per-Account; creating one requires a Clerk sign-in. Clerk's free
**Development instances** are made for local use — `pk_test_` / `sk_test_` keys
work on any `localhost` port with no domain setup, and Google social login works
on shared dev credentials. One-time:

1. Create a free app in the [Clerk dashboard](https://dashboard.clerk.com) (a
   Development instance is the default).
2. Copy the two dev keys into `.env`:
   - `VITE_CLERK_PUBLISHABLE_KEY=pk_test_…` (frontend)
   - `CLERK_SECRET_KEY=sk_test_…` (backend)
3. `docker compose restart frontend backend`.

The backend verifies session JWTs networklessly via JWKS; the frontend only
mounts Clerk when the publishable key is present.

## Repository layout

```
frontend/   React 19 + Vite + TS · react-router · TanStack Query · zustand
backend/    FastAPI · SQLAlchemy 2 (async) + Alembic · pydantic-settings · uv
docs/       ANALYSIS.md · PLAN.md · adr/ (architecture decisions) · research/
CONTEXT.md  domain glossary
```

## Testing

Backend API and scoring tests run with pytest. The API tests need a Postgres —
they use a dedicated `bigfive_test` database (never the app's data) reachable on
the host. With the Compose stack up:

```bash
docker compose exec -T db psql -U bigfive -d bigfive -c "CREATE DATABASE bigfive_test"  # one-time
cd backend && DB_PORT=<host-db-port> .venv/bin/pytest   # DB_PORT matches your .env (default 5432)
```

Tests that need the database are skipped automatically if it is unreachable, so
the scoring/parity/health tests still run without one.

Frontend type-check + production build:

```bash
docker compose exec -T frontend npm run build
```

### End-to-end (Playwright)

One happy-path spec (`frontend/e2e/happy-path.spec.ts`) drives the real UI against
the running Compose stack: start → select Quick → autofill 60 items → assert the
domain-only report (5 bars + narrative) → check the PDF endpoint returns `%PDF`.
It needs `VITE_TEST_MODE=true` (for the autofill control) and runs on the **host**
(Playwright is a host-side devDependency, not in the container). With the stack
up:

```bash
cd frontend
npm install                 # once, to pull @playwright/test
npm run e2e:install         # once, to download the Chromium browser
npm run e2e                 # runs against http://localhost:15173
```

Point it at a different frontend with `FRONTEND_URL=http://host:port npm run e2e`.

### Test mode (dev only)

Set `VITE_TEST_MODE=true` in `.env` to expose hidden controls that drive a full
run fast without hand-answering every item (120 on Full, 60 on Quick):

- **Start screen** — demographics are prefilled (age 30, male) so a run begins in
  one click.
- **Test screen** — a dashed **"⚡ Autofill & finish"** button answers every
  remaining item with a random 1–5 through the normal answer path, then completes
  the run and jumps to the report.

With the flag unset (the default) these controls are absent from the DOM. Never
enable test mode in production.

## Documentation

- **[docs/PLAN.md](docs/PLAN.md)** — development plan and PR sequence
- **[CONTEXT.md](CONTEXT.md)** — the domain language (Profile, Form, Test Run, …)
- **[docs/adr/](docs/adr/)** — architecture decision records
- **[docs/ANALYSIS.md](docs/ANALYSIS.md)** — source analysis behind the plan

Each part also has its own README: [`frontend/`](frontend/README.md) ·
[`backend/`](backend/README.md).
