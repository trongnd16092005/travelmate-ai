import pytest
from httpx import ASGITransport, AsyncClient

from app.clients.llm.base import ChatMessage
from app.main import app
from app.schemas.chat import ChatRequest
from app.services.chat import ChatService


class CapturingChatModel:
    def __init__(self, reply: str = "Lịch trình phù hợp.") -> None:
        self.reply = reply
        self.messages: list[ChatMessage] = []

    def generate(self, messages: list[ChatMessage]) -> str:
        self.messages = messages
        return self.reply


@pytest.mark.asyncio
async def test_chat_endpoint_uses_mock_provider() -> None:
    transport = ASGITransport(app=app)
    payload = {
        "message": "Tư vấn lịch trình Đà Nẵng",
        "tripContext": {
            "destination": "Đà Nẵng",
            "budgetVnd": 5000000,
            "numPeople": 2,
        },
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/internal/v1/ai/chat", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["isOutOfScope"] is False
    assert len(body["suggestedQuestions"]) == 3


@pytest.mark.asyncio
async def test_chat_endpoint_accepts_expo_web_origin() -> None:
    transport = ASGITransport(app=app)
    headers = {
        "Origin": "http://localhost:8081",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options("/internal/v1/ai/chat", headers=headers)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_chat_service_injects_trip_context_and_history() -> None:
    model = CapturingChatModel()
    service = ChatService(model, "mock")
    request = ChatRequest.model_validate(
        {
            "message": "Ngày thứ hai nên đi đâu?",
            "history": [
                {"role": "user", "content": "Tôi muốn đi biển"},
                {"role": "assistant", "content": "Bạn có thể đi Mỹ Khê"},
            ],
            "tripContext": {"destination": "Đà Nẵng", "numPeople": 2},
        }
    )

    response = service.chat(request)

    assert response.reply == "Lịch trình phù hợp."
    assert "Điểm đến: Đà Nẵng" in model.messages[1]["content"]
    assert model.messages[-1] == {"role": "user", "content": "Ngày thứ hai nên đi đâu?"}


def test_chat_service_removes_out_of_scope_marker() -> None:
    model = CapturingChatModel("[OUT_OF_SCOPE] Mình chỉ hỗ trợ du lịch.")
    service = ChatService(model, "mock")

    response = service.chat(ChatRequest(message="Viết code Java"))

    assert response.is_out_of_scope is True
    assert response.reply == "Mình chỉ hỗ trợ du lịch."
