import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes.chat import get_chat_service
from app.clients.llm.base import ChatMessage
from app.clients.llm.mock import MockChatModel
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
    app.dependency_overrides[get_chat_service] = lambda: ChatService(MockChatModel(), "mock")
    transport = ASGITransport(app=app)
    payload = {
        "message": "Tư vấn lịch trình Đà Nẵng",
        "tripContext": {
            "destination": "Đà Nẵng",
            "budgetVnd": 5000000,
            "numPeople": 2,
        },
    }

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/internal/v1/ai/chat", json=payload)
    finally:
        app.dependency_overrides.clear()

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
            "tripContext": {
                "destination": "Đà Nẵng",
                "startDate": "2026-08-20",
                "endDate": "2026-08-22",
                "numPeople": 2,
            },
        }
    )

    response = service.chat(request)

    assert response.reply == "Lịch trình phù hợp."
    assert "Điểm đến: Đà Nẵng" in model.messages[1]["content"]
    assert "Ngày bắt đầu: 2026-08-20" in model.messages[1]["content"]
    assert "Ngày kết thúc: 2026-08-22" in model.messages[1]["content"]
    assert model.messages[-1] == {"role": "user", "content": "Ngày thứ hai nên đi đâu?"}


def test_chat_memory_uses_latest_user_details_instead_of_form_defaults() -> None:
    model = CapturingChatModel("Mình đã ghi nhận thông tin mới.")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "10 triệu",
            "history": [
                {"role": "user", "content": "Tôi cần chuyến miền Trung cho 6 người"},
                {"role": "assistant", "content": "Bạn muốn đi đâu?"},
                {"role": "user", "content": "Huế, 3 ngày"},
                {"role": "assistant", "content": "Ngân sách dự kiến là bao nhiêu?"},
            ],
            "tripContext": {
                "destination": "Đà Nẵng",
                "budgetVnd": 5000000,
                "numPeople": 2,
            },
        }
    )

    service.chat(request)

    memory_message = model.messages[1]["content"]
    assert "Khu vực mong muốn: Miền Trung" in memory_message
    assert "Điểm đến: Huế" in memory_message
    assert "Thời lượng: 3 ngày" in memory_message
    assert "Số người: 6" in memory_message
    assert "Tổng ngân sách: 10,000,000 VND" in memory_message
    assert "Đà Nẵng" not in memory_message


def test_chat_replaces_repeated_reply_with_next_missing_question() -> None:
    repeated = "Mình chưa có thông tin điểm đến, số ngày hoặc ngân sách cho chuyến này."
    model = CapturingChatModel(repeated)
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "Huế, 3 ngày",
            "history": [
                {"role": "user", "content": "Tôi cần chuyến miền Trung cho 6 người"},
                {"role": "assistant", "content": repeated},
            ],
        }
    )

    response = service.chat(request)

    assert (
        response.reply
        == "Mình đã ghi nhận số người và thời lượng. Tổng ngân sách dự kiến là bao nhiêu?"
    )


def test_chat_repeated_reply_can_recommend_central_destinations() -> None:
    repeated = "Mình chưa có thông tin điểm đến, số ngày hoặc ngân sách cho chuyến này."
    model = CapturingChatModel(repeated)
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "Bạn hãy gợi ý điểm đến",
            "history": [
                {"role": "user", "content": "Tôi cần chuyến miền Trung cho 6 người"},
                {"role": "assistant", "content": repeated},
            ],
        }
    )

    response = service.chat(request)

    assert "Huế" in response.reply
    assert "Đà Nẵng–Hội An" in response.reply
    assert "Quảng Bình" in response.reply
    assert "6 người" in response.reply


def test_chat_replaces_missing_claim_that_conflicts_with_memory() -> None:
    model = CapturingChatModel(
        "Mình chưa có thông tin điểm đến, số ngày hoặc ngân sách cho chuyến này."
    )
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "10 triệu",
            "history": [
                {"role": "user", "content": "Tôi cần chuyến miền Trung cho 6 người"},
                {"role": "assistant", "content": "Bạn hãy chọn một điểm đến."},
                {"role": "user", "content": "Huế, 3 ngày"},
                {"role": "assistant", "content": "Tổng ngân sách dự kiến là bao nhiêu?"},
            ],
        }
    )

    response = service.chat(request)

    assert "Huế 3 ngày" in response.reply
    assert "6 người" in response.reply
    assert "10,000,000 VND" in response.reply


def test_chat_service_removes_out_of_scope_marker() -> None:
    model = CapturingChatModel("[OUT_OF_SCOPE] Mình chỉ hỗ trợ du lịch.")
    service = ChatService(model, "mock")

    response = service.chat(ChatRequest(message="Nấu món này giúp tôi"))

    assert response.is_out_of_scope is True
    assert response.reply == "Mình chỉ hỗ trợ du lịch."


def test_out_of_scope_guardrail_does_not_call_model() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Viết code Java sắp xếp mảng cho tôi"))

    assert response.is_out_of_scope is True
    assert model.messages == []


def test_transaction_guardrail_does_not_call_model() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Đặt luôn phòng rồi trừ tiền trong thẻ của tôi"))

    assert response.is_out_of_scope is False
    assert "không thể tự thực hiện giao dịch" in response.reply
    assert model.messages == []


def test_medical_guardrail_prioritizes_safety_without_calling_model() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Tôi đang sốt, uống thuốc gì để mai vẫn bay?"))

    assert response.is_out_of_scope is False
    assert "Ưu tiên an toàn" in response.reply
    assert model.messages == []


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Mai mưa lớn nhưng tôi vẫn chạy xe qua đèo Mã Pì Lèng", "không nên tiếp tục"),
        ("Tôi dị ứng hải sản nhưng muốn thử đặc sản", "không thể bảo đảm"),
        ("Đưa bố mẹ hơn 70 tuổi đi Ninh Bình", "ưu tiên lịch nhẹ"),
    ],
)
def test_safety_guardrails_do_not_call_model(message: str, expected: str) -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message=message))

    assert expected in response.reply
    assert model.messages == []


def test_chat_rejects_known_place_from_another_destination() -> None:
    model = CapturingChatModel("Bạn có thể ghé chùa Thiên Mụ và nghỉ ngơi.")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Lập lịch Ninh Bình cho hai người"))

    assert "chưa khớp với Ninh Bình" in response.reply


def test_chat_allows_explicitly_named_neighboring_destination() -> None:
    reply = "Bạn có thể di chuyển sang phố cổ Hội An rồi về lại Đà Nẵng trong ngày."
    model = CapturingChatModel(reply)
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Lập lịch Đà Nẵng cho hai người"))

    assert response.reply == reply


def test_chat_replaces_echoed_user_message() -> None:
    message = "Tôi muốn đi qua đèo vào ngày mai"
    model = CapturingChatModel(message)
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message=message))

    assert "chưa tạo được câu trả lời đủ tin cậy" in response.reply


def test_chat_converts_markdown_to_plain_text() -> None:
    model = CapturingChatModel("### Gợi ý\n\n* **Ăn sáng:** mì Quảng\n* `Đi bộ` nhẹ")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Gợi ý ngắn cho Đà Nẵng"))

    assert response.reply == "Gợi ý\n\n• Ăn sáng: mì Quảng\n• Đi bộ nhẹ"
