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

## Repository layout

```
frontend/   React 19 + Vite + TS · react-router · TanStack Query · zustand
backend/    FastAPI · SQLAlchemy 2 (async) + Alembic · pydantic-settings · uv
docs/       ANALYSIS.md · PLAN.md · adr/ (architecture decisions) · research/
CONTEXT.md  domain glossary
```

## Documentation

- **[docs/PLAN.md](docs/PLAN.md)** — development plan and PR sequence
- **[CONTEXT.md](CONTEXT.md)** — the domain language (Profile, Form, Test Run, …)
- **[docs/adr/](docs/adr/)** — architecture decision records
- **[docs/ANALYSIS.md](docs/ANALYSIS.md)** — source analysis behind the plan

Each part also has its own README: [`frontend/`](frontend/README.md) ·
[`backend/`](backend/README.md).
