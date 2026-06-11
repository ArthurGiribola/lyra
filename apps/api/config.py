from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = "development"
    port: int = 8000

    # Sprint 1 — banco de dados
    database_url: str | None = None

    # Sprint 1 — Spotify
    spotify_client_id: str | None = None
    spotify_client_secret: str | None = None

    # Sprint 1 — Genius
    genius_api_key: str | None = None


settings = Settings()
