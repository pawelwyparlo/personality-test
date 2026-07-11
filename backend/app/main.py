from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import forms, health, reports, test_runs
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Big Five API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(forms.router, prefix="/api/v1")
    app.include_router(test_runs.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    return app


app = create_app()
