from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TravelMate AI Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    core_api_url: str = "http://localhost:8080"
    llm_provider: str = "mock"
    gemini_api_key: str = ""
    openai_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

