from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from the environment / .env.

    The app must run with none of the LLM/Clerk keys set, so every optional
    integration credential defaults to an empty string and is validated where
    it is actually used, not here.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database — async SQLAlchemy URL (postgresql+asyncpg://...).
    database_url: str = "postgresql+asyncpg://bigfive:bigfive@localhost:5432/bigfive"

    # CORS origins allowed to call the API (the Vite dev server).
    cors_origins: list[str] = ["http://localhost:5173"]

    # LLM / Vertex AI — optional; report falls back to the text bank without them.
    google_cloud_project: str = ""
    vertex_location: str = "us-central1"

    # Clerk — optional; the coach gate shows a setup notice without them.
    clerk_secret_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
