from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Values are read (in order of priority):
      1. Environment variables (e.g. APP_NAME=... in the shell)
      2. A .env file in the backend/ directory
      3. The defaults defined below
    """

    # --- App metadata ---
    app_name: str = "CyberSentinel API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    # --- API ---
    api_v1_prefix: str = "/api/v1"

    # --- CORS ---
    # Comma-separated list of allowed origins.
    # Example: "http://localhost:5173,https://example.com"
    cors_origins: str = "http://localhost:5173"

    # --- ML model ---
    model_path: str = "../ml/models/random_forest_v2_top40.joblib"

    # --- Database ---
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/cybersentinel"
    db_echo: bool = False

    # --- Auth ---
    secret_key: str = "CHANGE_ME_IN_ENV"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Pydantic v2 config: read from .env, ignore unknown keys.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Caching means the .env file is only read once per process.
    """
    return Settings()
