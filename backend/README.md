# Big Five — Backend

FastAPI + SQLAlchemy 2 (async) + Alembic, managed with [`uv`](https://docs.astral.sh/uv/).

## Local development (without Docker)

```bash
uv sync                                    # install deps into .venv
uv run alembic upgrade head                # apply migrations
uv run uvicorn app.main:app --reload       # serve on :8000
uv run pytest                              # tests
```

Configuration comes from the repo-root `.env` (see `../.env.example`). The app
runs with no LLM/Clerk keys set. In Docker Compose the backend is built from
`Dockerfile` and started for you — see the repo `README.md`.

## Layout

- `app/main.py` — app factory + CORS
- `app/core/` — settings (`config.py`), async engine/session (`db.py`)
- `app/api/v1/` — versioned routers (`health`, `forms`, `test_runs`, `reports`,
  `coach`)
- `app/auth/clerk.py` — Clerk session-JWT verification (`require_account`);
  503 `auth_not_configured` when keyless, verifier injectable for tests
- `app/scoring/` · `app/report/` · `app/coach/` — scoring engine, report
  narrative (LLM + text-bank fallback), coach prompt/schemas
- `app/llm/` — thin `LLMClient` (Vertex + Null), `generate_structured` +
  `stream_text`
- `alembic/` — async migration environment
- `tests/` — pytest (httpx ASGI); coach tests use a fake Clerk verifier + fake
  streaming LLM

## Coach auth (Clerk)

The `/api/v1/coach*` endpoints are gated by `require_account`, which verifies the
Clerk session JWT (`Authorization: Bearer …`) networkless via the official SDK.
Keyless (`CLERK_SECRET_KEY` unset) they return 503 `auth_not_configured` — never
a crash. The coach chat streams over SSE and needs an LLM key; without one,
`POST /coach/messages` returns 503 `llm_not_configured` before persisting.
