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
    # Auth is either a service-account file (google_application_credentials, read
    # by the SDK's default credentials) or an API key (vertex_api_key). With
    # neither project+credentials nor an API key set, the factory yields a
    # NullClient and the report uses the deterministic text bank.
    google_cloud_project: str = ""
    vertex_location: str = "us-central1"
    google_application_credentials: str = ""
    vertex_api_key: str = ""
    # A current Gemini flash model; overridable per deployment.
    vertex_model: str = "gemini-2.0-flash-001"

    # Clerk — optional; the coach gate shows a setup notice without them.
    clerk_secret_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
