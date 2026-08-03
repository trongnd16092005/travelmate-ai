from types import SimpleNamespace
from typing import Any

import pytest

from app.clients.llm.base import GeminiModelUnavailableError
from app.clients.llm.factory import create_chat_model
from app.clients.llm.gemini import GeminiChatModel
from app.core.config import Settings


class FakeGeminiModels:
    def __init__(self, reply: str = "Lịch trình Gemini.") -> None:
        self.reply = reply
        self.request: dict[str, Any] = {}

    def generate_content(self, **kwargs: Any) -> SimpleNamespace:
        self.request = kwargs
        return SimpleNamespace(text=self.reply)


def gemini_settings(**overrides: Any) -> Settings:
    values = {"llm_provider": "gemini", "gemini_api_key": "test-key"}
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_gemini_maps_system_prompt_and_chat_history() -> None:
    models = FakeGeminiModels()
    client = SimpleNamespace(models=models)
    model = GeminiChatModel(gemini_settings(), client=client)

    reply = model.generate(
        [
            {"role": "system", "content": "Bạn là TravelMate."},
            {"role": "system", "content": "Điểm đến: Đà Nẵng"},
            {"role": "assistant", "content": "Chào bạn, mình là TravelMate."},
            {"role": "user", "content": "Tôi muốn đi biển"},
            {"role": "assistant", "content": "Bạn đi mấy ngày?"},
            {"role": "user", "content": "Ba ngày"},
        ]
    )

    assert reply == "Lịch trình Gemini."
    assert models.request["model"] == "gemini-2.5-flash"
    assert models.request["config"]["system_instruction"] == (
        "Bạn là TravelMate.\n\nĐiểm đến: Đà Nẵng"
    )
    assert [content["role"] for content in models.request["contents"]] == [
        "user",
        "model",
        "user",
    ]


def test_gemini_requires_api_key() -> None:
    model = GeminiChatModel(gemini_settings(gemini_api_key=""))

    with pytest.raises(GeminiModelUnavailableError, match="GEMINI_API_KEY"):
        model.generate([{"role": "user", "content": "Đi Đà Nẵng"}])


def test_factory_selects_gemini_provider() -> None:
    model = create_chat_model(gemini_settings())

    assert isinstance(model, GeminiChatModel)
