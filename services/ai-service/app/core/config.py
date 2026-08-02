from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TravelMate AI Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    core_api_url: str = "http://localhost:8080"
    llm_provider: Literal["mock", "local"] = "mock"
    local_model_id: str = "Qwen/Qwen3-4B"
    local_adapter_path: str = "artifacts/travelmate-qwen3-4b-lora"
    local_model_device: str = "auto"
    local_model_load_in_4bit: bool = False
    local_model_max_new_tokens: int = 512
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
