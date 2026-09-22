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

    # --- CORS (used later by the React frontend) ---
    cors_origins: list[str] = ["http://localhost:5173"]
        # --- ML model ---
    # Path to the joblib bundle. Relative paths are resolved from the
    # process working directory (backend/ when running uvicorn).
    model_path: str = "../ml/models/random_forest_v2_top40.joblib"

        # --- Database ---
    database_url: str = "postgresql+psycopg://postgres:Kiprop%4003@localhost:5432/cybersentinel"
    db_echo: bool = False

    # --- Database ---
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/cybersentinel"
    db_echo: bool = False
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
