import re
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TravelMate AI Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    core_api_url: str = "http://localhost:8080"
    cors_origins: str = (
        "http://localhost:8081,http://127.0.0.1:8081,http://localhost:19006,http://127.0.0.1:19006"
    )
    llm_provider: Literal["mock", "gemini", "local"] = "mock"
    local_model_id: str = "Qwen/Qwen3-4B"
    local_adapter_path: str = "artifacts/travelmate-qwen3-4b-lora-v10-reasoning-guarded"
    local_model_device: str = "auto"
    local_model_load_in_4bit: bool = True
    local_model_max_new_tokens: int = 512
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_temperature: float = 0.4
    gemini_max_output_tokens: int = 1536
    openai_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def local_model_version(self) -> str | None:
        match = re.search(r"(?:^|[-_/])(v\d+)(?:[-_/]|$)", self.local_adapter_path.casefold())
        return match.group(1) if match else None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
