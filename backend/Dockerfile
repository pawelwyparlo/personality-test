# Big Five backend image, built on the official uv base (Python 3.12).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# System dependencies.
# NOTE: WeasyPrint (PDF report generation, added in a later PR) needs the
# Pango/Cairo/GDK-Pixbuf native libraries here, e.g.:
#   RUN apt-get update && apt-get install -y --no-install-recommends \
#       libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev \
#       && rm -rf /var/lib/apt/lists/*
# Not installed yet — keep the image slim until the report PR needs them.

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (cached unless the lockfile/pyproject change).
# --no-install-project so this layer doesn't depend on the app source.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Application source (volume-mounted over this in Compose for --reload).
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Put the project venv on PATH so `uvicorn`/`alembic` resolve directly.
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
