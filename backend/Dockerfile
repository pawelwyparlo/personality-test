# Big Five backend image, built on the official uv base (Python 3.12).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# System dependencies.
# WeasyPrint (report PDF generation, PR4) needs the Pango/Cairo/GDK-Pixbuf
# native libraries at runtime. Fonts (DejaVu) make the deterministic template
# render identically across hosts.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
        libffi-dev libharfbuzz0b libfontconfig1 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

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
