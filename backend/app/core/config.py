from functools import lru_cache
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_is_pytest = bool(os.getenv("PYTEST_CURRENT_TEST"))


class Settings(BaseSettings):
    environment: str = Field(default="development", alias="ENVIRONMENT")
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    database_url: str = Field(default="", alias="DATABASE_URL")
    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_refresh_secret: str = Field(default="change-me-refresh", alias="JWT_REFRESH_SECRET")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # During pytest runs we avoid loading the .env file so tests can control
    # environment via monkeypatch without interference from a repo .env file.
    model_config = SettingsConfigDict(env_file=None if _is_pytest else ".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

