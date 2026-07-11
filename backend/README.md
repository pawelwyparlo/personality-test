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
- `app/api/v1/` — versioned routers (`health.py`)
- `alembic/` — async migration environment
- `tests/` — pytest (httpx ASGI)
