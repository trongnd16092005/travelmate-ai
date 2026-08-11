from typing import Any

import httpx
import pytest

from app.clients.llm.base import GroqModelUnavailableError
from app.clients.llm.factory import create_chat_model
from app.clients.llm.groq import GroqChatModel
from app.core.config import Settings


class FakeGroqClient:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.request: dict[str, Any] = {}

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        self.request = {"url": url, **kwargs}
        return self.response


def groq_response(status_code: int, payload: dict[str, Any] | None = None) -> httpx.Response:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return httpx.Response(status_code, request=request, json=payload or {})


def groq_settings(**overrides: Any) -> Settings:
    values = {
        "llm_provider": "groq",
        "groq_api_key": "test-key",
        "groq_max_retries": 0,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_groq_maps_messages_and_generation_options() -> None:
    response = groq_response(
        200,
        {"choices": [{"message": {"content": "  Lịch trình Groq.  "}}]},
    )
    client = FakeGroqClient(response)
    model = GroqChatModel(groq_settings(), client=client)
    messages = [
        {"role": "system", "content": "Bạn là TravelMate."},
        {"role": "user", "content": "Lên lịch đi Huế."},
    ]

    reply = model.generate(messages)

    assert reply == "Lịch trình Groq."
    assert client.request["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert client.request["json"] == {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.2,
        "max_completion_tokens": 1536,
    }
    assert client.request["headers"]["authorization"] == "Bearer test-key"


def test_groq_requires_api_key() -> None:
    model = GroqChatModel(groq_settings(groq_api_key=""))

    with pytest.raises(GroqModelUnavailableError, match="GROQ_API_KEY"):
        model.generate([{"role": "user", "content": "Đi Huế"}])


def test_groq_rejects_empty_completion() -> None:
    client = FakeGroqClient(groq_response(200, {"choices": []}))
    model = GroqChatModel(groq_settings(), client=client)

    with pytest.raises(GroqModelUnavailableError, match="không trả về nội dung"):
        model.generate([{"role": "user", "content": "Đi Huế"}])


def test_groq_maps_authentication_error_without_leaking_response() -> None:
    client = FakeGroqClient(groq_response(401, {"error": {"message": "private details"}}))
    model = GroqChatModel(groq_settings(), client=client)

    with pytest.raises(GroqModelUnavailableError, match="GROQ_API_KEY") as error:
        model.generate([{"role": "user", "content": "Đi Huế"}])

    assert "private details" not in str(error.value)


def test_factory_selects_groq_provider() -> None:
    model = create_chat_model(groq_settings())

    assert isinstance(model, GroqChatModel)
