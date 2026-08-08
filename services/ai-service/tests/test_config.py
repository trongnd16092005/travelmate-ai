from app.core.config import Settings


def test_settings_extracts_local_adapter_version() -> None:
    settings = Settings(
        _env_file=None,
        local_adapter_path="artifacts/travelmate-qwen3-4b-lora-v7-intent-execution",
    )

    assert settings.local_model_version == "v7"


def test_settings_allows_adapter_without_version() -> None:
    settings = Settings(_env_file=None, local_adapter_path="artifacts/custom-adapter")

    assert settings.local_model_version is None
