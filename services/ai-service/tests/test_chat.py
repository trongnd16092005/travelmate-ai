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
            "message": "Tư vấn thêm cho chuyến đi",
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
    assert model.messages[-1] == {"role": "user", "content": "Tư vấn thêm cho chuyến đi"}


def test_chat_only_sends_eight_recent_raw_messages_to_model() -> None:
    model = CapturingChatModel()
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "Tiếp tục giúp tôi",
            "history": [
                {"role": "user", "content": "tin rất cũ"},
                {"role": "assistant", "content": "trả lời rất cũ"},
                {"role": "user", "content": "tin cũ hơn"},
                {"role": "assistant", "content": "trả lời cũ hơn"},
                {"role": "user", "content": "tin cũ 1"},
                {"role": "assistant", "content": "trả lời cũ 1"},
                {"role": "user", "content": "tin cũ 2"},
                {"role": "assistant", "content": "trả lời cũ 2"},
                {"role": "user", "content": "tin mới"},
                {"role": "assistant", "content": "trả lời mới"},
            ],
        }
    )

    service.chat(request)

    raw_contents = [message["content"] for message in model.messages]
    assert "tin rất cũ" not in raw_contents
    assert "trả lời rất cũ" not in raw_contents
    assert raw_contents[-9:] == [
        "tin cũ hơn",
        "trả lời cũ hơn",
        "tin cũ 1",
        "trả lời cũ 1",
        "tin cũ 2",
        "trả lời cũ 2",
        "tin mới",
        "trả lời mới",
        "Tiếp tục giúp tôi",
    ]


def test_chat_memory_reads_twenty_messages_but_model_only_gets_eight() -> None:
    model = CapturingChatModel()
    service = ChatService(model, "local")
    filler = [
        {"role": "assistant" if index % 2 else "user", "content": f"tin đệm {index}"}
        for index in range(12)
    ]
    request = ChatRequest.model_validate(
        {
            "message": "Tư vấn tiếp",
            "history": [
                {"role": "user", "content": "Mình đi Huế, thích ẩm thực và lịch thư thả."},
                {"role": "assistant", "content": "Mình đã ghi nhận."},
                *filler,
            ],
        }
    )

    messages = service.build_messages(request)
    raw_contents = [message["content"] for message in messages]

    assert "Điểm đến: Huế" in messages[1]["content"]
    assert "Ưu tiên trải nghiệm: ẩm thực" in messages[1]["content"]
    assert "Mình đi Huế, thích ẩm thực và lịch thư thả." not in raw_contents[3:]
    assert len(raw_contents[3:-1]) == 8


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("rồi", "đã bao gồm chi phí di chuyển"),
        ("chưa", "chưa bao gồm chi phí di chuyển"),
    ],
)
def test_chat_understands_short_transport_answer(answer: str, expected: str) -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": answer,
            "history": [
                {"role": "user", "content": "Mình muốn đi Huế với nhóm bạn."},
                {"role": "assistant", "content": "Bạn dự định đi bao nhiêu ngày?"},
                {
                    "role": "user",
                    "content": "Bọn mình đi 3 ngày, thích ăn uống và không muốn lịch quá dày.",
                },
                {"role": "assistant", "content": "Chuyến này có bao nhiêu người?"},
                {"role": "user", "content": "4 người"},
                {"role": "assistant", "content": "Tổng ngân sách dự kiến là bao nhiêu?"},
                {"role": "user", "content": "15 triệu"},
                {
                    "role": "assistant",
                    "content": "Ngân sách này đã gồm chi phí di chuyển đến điểm đến chưa?",
                },
            ],
        }
    )

    response = service.chat(request)

    assert expected in response.reply
    assert "Ngân sách này đã gồm" not in response.reply
    assert model.messages == []


def test_chat_answers_preparation_intent_without_resuming_slot_questions() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "Cần chuẩn bị những gì cho chuyến đi?",
            "history": [
                {"role": "user", "content": "Huế, 3 ngày, 4 người, 15 triệu"},
                {
                    "role": "assistant",
                    "content": "Ngân sách này đã gồm chi phí di chuyển đến điểm đến chưa?",
                },
            ],
        }
    )

    response = service.chat(request)

    assert "giấy tờ tùy thân" in response.reply
    assert "Checklist cho Huế trong 3 ngày" in response.reply
    assert "gợi ý điểm đến theo khu vực" not in response.reply
    assert model.messages == []


def test_chat_keeps_destination_when_user_mentions_its_region() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "miền trung",
            "history": [
                {"role": "user", "content": "Mình đang lên chuyến Huế 3 ngày cho 4 người"},
                {"role": "assistant", "content": "Bạn muốn ưu tiên khu vực nào?"},
            ],
        }
    )

    response = service.chat(request)

    assert "Huế thuộc Miền Trung" in response.reply
    assert "vẫn giữ Huế là điểm đến" in response.reply
    assert model.messages == []


def test_chat_switches_from_completed_destination_to_new_region() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "tôi muốn đi du lịch miền bắc",
            "history": [
                {"role": "user", "content": "đi Đà Nẵng"},
                {"role": "assistant", "content": "Bạn đi bao nhiêu ngày?"},
                {"role": "user", "content": "3 ngày, 2 người, 10 triệu"},
                {
                    "role": "assistant",
                    "content": "Ngân sách đã gồm chi phí di chuyển chưa?",
                },
                {"role": "user", "content": "chưa"},
                {
                    "role": "assistant",
                    "content": "Bạn muốn lập lịch, phân bổ ngân sách hay checklist?",
                },
            ],
            "tripContext": {
                "destination": "Đà Nẵng",
                "budgetVnd": 5000000,
                "numPeople": 2,
            },
        }
    )

    response = service.chat(request)

    assert "chuyến Miền Bắc" in response.reply
    assert "biển, văn hóa hay thiên nhiên" in response.reply
    assert "Đà Nẵng" not in response.reply
    assert "10.000.000" not in response.reply
    assert model.messages == []


@pytest.mark.parametrize(
    "message",
    [
        "chuyển qua Tây Nguyên",
        "đổi qua Tây Nguyên",
        "chuyến tiếp theo chuyển qua Tây Nguyên",
        "giờ muốn khám phá Tây Nguyên",
    ],
)
def test_chat_region_switch_paraphrases_discard_destination_slots(message: str) -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(_completed_da_nang_request(message))

    assert "Tây Nguyên" in response.reply
    assert "Đà Nẵng" not in response.reply
    assert "10.000.000" not in response.reply
    assert "3 ngày" not in response.reply
    assert "2 người" not in response.reply
    assert model.messages == []


def test_chat_natural_reset_clears_context_and_returns_ui_signal() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local", "v7")
    request = ChatRequest.model_validate(
        {
            "message": "xóa thông tin chuyến cũ",
            "history": [
                {"role": "user", "content": "Đà Nẵng 3 ngày, 2 người, 10 triệu"},
                {"role": "assistant", "content": "Mình đã ghi nhận."},
            ],
        }
    )

    response = service.chat(request)

    assert response.reset_context is True
    assert response.model_version == "v7"
    assert "đã xóa ngữ cảnh chuyến cũ" in response.reply
    assert response.suggested_questions == [
        "Gợi ý điểm đến miền Bắc",
        "Gợi ý điểm đến miền Trung",
        "Gợi ý điểm đến miền Nam",
    ]
    assert model.messages == []


def _completed_da_nang_request(message: str) -> ChatRequest:
    return ChatRequest.model_validate(
        {
            "message": message,
            "history": [
                {"role": "user", "content": "đi Đà Nẵng"},
                {"role": "assistant", "content": "Bạn đi bao nhiêu ngày?"},
                {"role": "user", "content": "3 ngày, 2 người, 10 triệu"},
                {
                    "role": "assistant",
                    "content": "Ngân sách đã gồm chi phí di chuyển chưa?",
                },
                {"role": "user", "content": "chưa"},
                {"role": "assistant", "content": "Mình đã ghi nhận chuyến đi."},
            ],
        }
    )


@pytest.mark.parametrize(
    "message,new_destination",
    [
        ("đổi sang Huế", "Huế"),
        ("giờ tôi muốn đi Cần Thơ", "Cần Thơ"),
        ("chuyển qua Phú Quốc nhé", "An Giang"),
        ("thay bằng Hà Giang", "Tuyên Quang"),
    ],
)
def test_chat_new_destination_resets_trip_scoped_slots(
    message: str, new_destination: str
) -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(_completed_da_nang_request(message))

    assert f"điểm đến {new_destination}" in response.reply
    assert "bao nhiêu ngày" in response.reply
    assert "10.000.000" not in response.reply
    assert "2 người" not in response.reply
    assert model.messages == []


@pytest.mark.parametrize(
    ("message", "new_destination"),
    [
        ("chọn Hà Giang thay cho Đà Nẵng", "Tuyên Quang"),
        ("chọn Hà Giang thay vì Đà Nẵng", "Tuyên Quang"),
        ("thay Đà Nẵng bằng Hà Giang", "Tuyên Quang"),
        ("đổi từ Đà Nẵng sang Hà Giang", "Tuyên Quang"),
        ("chuyển từ Đà Nẵng qua Hà Giang", "Tuyên Quang"),
    ],
)
def test_chat_destination_replacement_selects_semantic_target(
    message: str,
    new_destination: str,
) -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(_completed_da_nang_request(message))

    assert f"điểm đến {new_destination}" in response.reply
    assert "bao nhiêu ngày" in response.reply
    assert "10.000.000" not in response.reply
    assert "2 người" not in response.reply
    assert model.messages == []


def test_chat_new_destination_uses_only_slots_supplied_in_same_message() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(
        _completed_da_nang_request("đổi sang Huế 4 ngày, 3 người, 12 triệu")
    )

    assert "Huế 4 ngày cho 3 người" in response.reply
    assert "12.000.000 VND" in response.reply
    assert "đã gồm chi phí di chuyển" in response.reply
    assert "Đà Nẵng" not in response.reply


def test_chat_slot_correction_does_not_reset_current_destination() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(_completed_da_nang_request("đổi ngân sách thành 12 triệu"))

    assert "Đà Nẵng 3 ngày cho 2 người" in response.reply
    assert "12.000.000 VND" in response.reply


def test_chat_multi_slot_followup_uses_progress_reply() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "4 ngày, 3 người, ngân sách 12 triệu",
            "history": [
                {"role": "user", "content": "Tôi muốn đi Hà Giang"},
                {"role": "assistant", "content": "Bạn dự định đi bao nhiêu ngày?"},
            ],
        }
    )

    response = service.chat(request)

    assert "Tuyên Quang 4 ngày cho 3 người" in response.reply
    assert "12.000.000 VND" in response.reply
    assert "đã gồm chi phí di chuyển" in response.reply
    assert model.messages == []


def test_chat_vague_planning_request_asks_natural_clarification() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Tôi muốn đi chơi vài hôm, tư vấn giúp"))

    assert "điểm đến hoặc khu vực nào" in response.reply
    assert "bao nhiêu ngày" in response.reply
    assert "ngân sách dự kiến" in response.reply
    assert model.messages == []


def test_chat_vague_planning_request_keeps_supplied_duration() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Tôi muốn đi chơi 4 ngày"))

    assert "chuyến 4 ngày" in response.reply
    assert "điểm đến hoặc khu vực nào" in response.reply
    assert model.messages == []


def test_chat_repeating_same_destination_does_not_reset_other_slots() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(_completed_da_nang_request("vẫn đi Đà Nẵng nhé"))

    assert "Đà Nẵng 3 ngày cho 2 người" in response.reply
    assert "10.000.000 VND" in response.reply


@pytest.mark.parametrize(
    "message",
    [
        "mình muốn làm lại từ đầu",
        "cho tôi bắt đầu một chuyến khác",
        "tôi muốn đi nơi khác",
        "đổi chuyến giúp tôi",
        "bắt đầu kế hoạch mới nhé",
    ],
)
def test_chat_reset_intent_supports_natural_paraphrases(message: str) -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local", "v7")

    response = service.chat(_completed_da_nang_request(message))

    assert response.reset_context is True
    assert "đã xóa ngữ cảnh chuyến cũ" in response.reply
    assert model.messages == []


def test_chat_memory_retains_pace_and_interests() -> None:
    service = ChatService(CapturingChatModel(), "local")
    request = ChatRequest.model_validate(
        {
            "message": "Tư vấn tiếp giúp mình",
            "history": [
                {
                    "role": "user",
                    "content": "Đi Huế 3 ngày, thích ăn uống và không muốn lịch quá dày.",
                },
                {"role": "assistant", "content": "Mình đã ghi nhận."},
            ],
        }
    )

    memory_message = service.build_messages(request)[1]["content"]

    assert "Nhịp chuyến đi: thư thả" in memory_message
    assert "Ưu tiên trải nghiệm: ẩm thực" in memory_message


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

    messages = service.build_messages(request)

    memory_message = messages[1]["content"]
    assert "Khu vực mong muốn: Miền Trung" in memory_message
    assert "Điểm đến: Huế" in memory_message
    assert "Thời lượng: 3 ngày" in memory_message
    assert "Số người: 6" in memory_message
    assert "Tổng ngân sách: 10,000,000 VND" in memory_message
    assert "Đà Nẵng" not in memory_message


def test_chat_discards_form_defaults_when_chat_changes_destination() -> None:
    service = ChatService(CapturingChatModel(), "local")
    request = ChatRequest.model_validate(
        {
            "message": "Bọn mình đi Huế 3 ngày, thích ăn uống và lịch thư thả.",
            "tripContext": {
                "destination": "Đà Nẵng",
                "budgetVnd": 5000000,
                "numPeople": 2,
            },
        }
    )

    memory_message = service.build_messages(request)[1]["content"]

    assert "Điểm đến: Huế" in memory_message
    assert "Thời lượng: 3 ngày" in memory_message
    assert "Số người" not in memory_message
    assert "Tổng ngân sách" not in memory_message


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
        response.reply == "Mình đã ghi nhận chuyến Huế 3 ngày cho 6 người. "
        "Tổng ngân sách dự kiến là bao nhiêu?"
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


def test_chat_guides_region_request_without_calling_model() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Gợi ý điểm đến miền Trung cho 6 người"))

    assert "Huế" in response.reply
    assert "Đà Nẵng–Hội An" in response.reply
    assert "6 người" in response.reply
    assert model.messages == []


def test_chat_region_planning_request_asks_for_preference_first() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Tôi cần chuyến miền Trung cho 6 người"))

    assert "Miền Trung cho 6 người" in response.reply
    assert "biển, văn hóa hay thiên nhiên" in response.reply
    assert model.messages == []


def test_chat_recommends_grounded_northern_beaches_from_demo_dialogue() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "gợi ý giúp tôi",
            "history": [
                {"role": "user", "content": "tôi cần đi du lịch ở miền bắc"},
                {
                    "role": "assistant",
                    "content": "Bạn muốn ưu tiên biển, văn hóa hay thiên nhiên?",
                },
                {"role": "user", "content": "biển"},
            ],
        }
    )

    response = service.chat(request)

    assert "Hạ Long" in response.reply
    assert "Cát Bà" in response.reply
    assert "Cô Tô" in response.reply
    assert "Hà Nội" not in response.reply
    assert "Sa Pa" not in response.reply
    assert model.messages == []


def test_chat_short_beach_answer_uses_region_and_theme_catalog() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "biển",
            "history": [
                {"role": "user", "content": "tôi cần đi du lịch ở miền bắc"},
                {
                    "role": "assistant",
                    "content": "Bạn muốn ưu tiên biển, văn hóa hay thiên nhiên?",
                },
            ],
        }
    )

    response = service.chat(request)

    assert "Với ưu tiên biển ở Miền Bắc" in response.reply
    assert "Hạ Long" in response.reply
    assert "Quan Lạn" in response.reply
    assert model.messages == []


def test_chat_short_destination_selection_does_not_load_model() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "Đi Hạ Long",
            "history": [
                {"role": "user", "content": "Gợi ý đi chơi ở miền bắc"},
                {
                    "role": "assistant",
                    "content": (
                        "Mình đã ghi nhận chuyến Miền Bắc. Bạn muốn ưu tiên biển, "
                        "văn hóa hay thiên nhiên để mình gợi ý điểm đến phù hợp?"
                    ),
                },
                {"role": "user", "content": "Thiên nhiên"},
                {
                    "role": "assistant",
                    "content": (
                        "Với ưu tiên thiên nhiên ở Miền Bắc, mình gợi ý: Sa Pa; "
                        "Ninh Bình; Hạ Long; Hà Giang; Cao Bằng. Bạn chọn một nơi."
                    ),
                },
            ],
        }
    )

    response = service.chat(request)

    assert "Hạ Long thuộc Quảng Ninh" in response.reply
    assert "bao nhiêu ngày" in response.reply
    assert model.messages == []


def test_chat_asks_for_clarification_on_mixed_typo() -> None:
    model = CapturingChatModel("không nên được gọi")
    response = ChatService(model, "local").chat(ChatRequest(message="2ngywofi"))

    assert "chưa hiểu rõ" in response.reply
    assert "2 người" in response.reply
    assert "3 ngày" in response.reply
    assert model.messages == []


def test_chat_does_not_guess_opening_hours_or_ticket_prices() -> None:
    model = CapturingChatModel("không nên được gọi")
    request = ChatRequest.model_validate(
        {
            "message": "Cho tôi biết giờ hoạt động và giá vé",
            "history": [
                {"role": "user", "content": "Đi Hà Nội 3 ngày"},
                {"role": "assistant", "content": "Mình đã ghi nhận Hà Nội."},
            ],
        }
    )

    response = ChatService(model, "local").chat(request)

    assert "nguồn realtime" in response.reply
    assert "Hà Nội" in response.reply
    assert "không tự đưa ra con số hay khung giờ" in response.reply
    assert model.messages == []


def test_hot_destination_recommends_expanded_catalog_unless_three_requested() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    expanded = service.chat(ChatRequest(message="Nên đi đâu ở Hà Nội?"))
    limited = service.chat(ChatRequest(message="Gợi ý ba điểm ở Hà Nội"))

    assert "6 điểm" in expanded.reply
    assert "Nhà tù Hỏa Lò" in expanded.reply
    assert "Hồ Tây" in expanded.reply
    assert "ba điểm" in limited.reply
    assert "Nhà tù Hỏa Lò" not in limited.reply
    assert model.messages == []


def _complete_ho_chi_minh_history() -> list[dict[str, str]]:
    return [
        {"role": "user", "content": "đi thành phố hồ chí minh"},
        {
            "role": "assistant",
            "content": "Mình đã ghi nhận điểm đến TP. Hồ Chí Minh. Bạn đi bao nhiêu ngày?",
        },
        {"role": "user", "content": "3 ngày 2 người với mức 10 triệu"},
        {
            "role": "assistant",
            "content": "Ngân sách này đã gồm chi phí di chuyển đến điểm đến chưa?",
        },
        {"role": "user", "content": "rồi"},
        {
            "role": "assistant",
            "content": "Bạn muốn lập lịch trình, phân bổ ngân sách hay chuẩn bị checklist?",
        },
    ]


def test_chat_executes_itinerary_intent_from_current_demo() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "hỗ trợ lập lịch đi",
            "history": _complete_ho_chi_minh_history(),
        }
    )

    response = service.chat(request)

    assert "Lịch gợi ý 3 ngày tại TP. Hồ Chí Minh cho 2 người" in response.reply
    assert "Ngày 1: sáng tham quan Dinh Độc Lập" in response.reply
    assert "Ngày 3:" in response.reply
    assert "Bạn muốn" not in response.reply
    assert model.messages == []


def test_chat_executes_budget_allocation_without_asking_again() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "phân bổ ngân sách giúp tôi",
            "history": _complete_ho_chi_minh_history(),
        }
    )

    response = service.chat(request)

    assert "Phân bổ tham khảo 10.000.000 VND" in response.reply
    assert "Lưu trú 35%: 3.500.000 VND" in response.reply
    assert "Di chuyển toàn chuyến 20%: 2.000.000 VND" in response.reply
    assert "Dự phòng 5%: 500.000 VND" in response.reply
    assert model.messages == []


def test_chat_executes_contextual_checklist_without_model() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "chuẩn bị checklist cho tôi",
            "history": _complete_ho_chi_minh_history(),
        }
    )

    response = service.chat(request)

    assert "Checklist cho TP. Hồ Chí Minh trong 3 ngày" in response.reply
    assert "Giấy tờ" in response.reply
    assert "thuốc đang dùng" in response.reply
    assert "cảnh báo địa phương" in response.reply
    assert model.messages == []


def test_chat_can_execute_itinerary_budget_and_checklist_together() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "lập lịch trình, phân bổ ngân sách và làm checklist luôn",
            "history": _complete_ho_chi_minh_history(),
        }
    )

    response = service.chat(request)

    assert "Lịch gợi ý 3 ngày" in response.reply
    assert "Phân bổ tham khảo 10.000.000 VND" in response.reply
    assert "Checklist cho TP. Hồ Chí Minh" in response.reply
    assert model.messages == []


def test_chat_recovers_from_demo_followup_theo_diem_den() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    history = _complete_ho_chi_minh_history()
    history.extend(
        [
            {"role": "user", "content": "hỗ trợ lập lịch đi"},
            {
                "role": "assistant",
                "content": (
                    "Bạn cần phân bổ ngân sách theo ngày hay muốn mình gợi ý điểm đến cụ thể?"
                ),
            },
        ]
    )

    response = service.chat(ChatRequest(message="theo điểm đến", history=history))

    assert "Lịch gợi ý 3 ngày tại TP. Hồ Chí Minh" in response.reply
    assert model.messages == []


def test_chat_guides_short_slot_reply_to_next_missing_field() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "Huế, 3 ngày",
            "history": [
                {"role": "user", "content": "Tôi cần chuyến miền Trung cho 6 người"},
                {"role": "assistant", "content": "Bạn có thể cân nhắc Huế."},
            ],
        }
    )

    response = service.chat(request)

    assert response.reply == (
        "Mình đã ghi nhận chuyến Huế 3 ngày cho 6 người. Tổng ngân sách dự kiến là bao nhiêu?"
    )
    assert model.messages == []


def test_chat_guides_detailed_slot_reply_without_slow_model_call() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": (
                "Bọn mình đi 3 ngày 2 đêm, thích ăn uống và không muốn lịch quá dày."
            ),
            "history": [
                {"role": "user", "content": "Mình muốn đi Huế với nhóm bạn."},
                {"role": "assistant", "content": "Bạn dự định đi bao nhiêu ngày?"},
            ],
        }
    )

    response = service.chat(request)

    assert response.reply == "Mình đã ghi nhận thời lượng chuyến đi. Chuyến này có bao nhiêu người?"
    assert model.messages == []


def test_chat_understands_hom_as_trip_duration() -> None:
    model = CapturingChatModel("không nên được gọi")
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message="Tầm 3 hôm ở Huế, có 2 người"))

    assert response.reply == (
        "Mình đã ghi nhận chuyến Huế 3 ngày cho 2 người. Tổng ngân sách dự kiến là bao nhiêu?"
    )
    assert model.messages == []


def test_chat_replaces_question_that_asks_two_missing_fields() -> None:
    model = CapturingChatModel(
        "Mình đã ghi nhận 3 ngày và 2 người. "
        "Bạn khởi hành ngày nào và dự kiến tổng ngân sách bao nhiêu?"
    )
    service = ChatService(model, "local")
    request = ChatRequest.model_validate(
        {
            "message": "Bạn tư vấn tiếp giúp mình",
            "history": [
                {"role": "user", "content": "Tầm 3 hôm ở Huế, có 2 người"},
                {"role": "assistant", "content": "Mình đã ghi nhận."},
            ],
        }
    )

    response = service.chat(request)

    assert response.reply.endswith("Tổng ngân sách dự kiến là bao nhiêu?")
    assert "khởi hành" not in response.reply


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
    assert "10.000.000 VND" in response.reply


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


def test_chat_replaces_known_place_from_another_destination_with_catalog() -> None:
    model = CapturingChatModel("Bạn có thể ghé chùa Thiên Mụ và nghỉ ngơi.")
    service = ChatService(model, "local")

    response = service.chat(
        ChatRequest.model_validate(
            {
                "message": "Bạn tư vấn tiếp giúp mình",
                "history": [
                    {"role": "user", "content": "Ninh Bình cho hai người"},
                    {"role": "assistant", "content": "Mình đã ghi nhận."},
                ],
            }
        )
    )

    assert "Ninh Bình" in response.reply
    assert "Tràng An" in response.reply
    assert "chùa Thiên Mụ" not in response.reply


def test_chat_allows_explicitly_named_neighboring_destination() -> None:
    reply = "Bạn có thể di chuyển sang phố cổ Hội An rồi về lại Đà Nẵng trong ngày."
    model = CapturingChatModel(reply)
    service = ChatService(model, "local")

    response = service.chat(
        ChatRequest.model_validate(
            {
                "message": "Bạn tư vấn tiếp giúp mình",
                "history": [
                    {"role": "user", "content": "Đà Nẵng cho hai người"},
                    {"role": "assistant", "content": "Mình đã ghi nhận."},
                ],
            }
        )
    )

    assert response.reply == reply


def test_chat_replaces_echoed_user_message() -> None:
    message = "Chia sẻ thêm chi tiết cho tôi"
    model = CapturingChatModel(message)
    service = ChatService(model, "local")

    response = service.chat(ChatRequest(message=message))

    assert "chưa tạo được câu trả lời đủ tin cậy" in response.reply


def test_chat_converts_markdown_to_plain_text() -> None:
    reply = ChatService._to_plain_text(
        "### Gợi ý\n\n* **Ăn sáng:** mì Quảng\n* `Đi bộ` nhẹ"
    )

    assert reply == "Gợi ý\n\n• Ăn sáng: mì Quảng\n• Đi bộ nhẹ"


@pytest.mark.parametrize(
    ("message", "expected_terms"),
    [
        (
            "Gia đình có trẻ nhỏ và người lớn tuổi đi Huế 4 ngày, muốn xem nhiều nơi nhưng không quá mệt.",
            ("ưu tiên sức khỏe", "Đại Nội", "thời gian nghỉ"),
        ),
        (
            "Nhóm 5 người có 7 triệu đi Đà Lạt 5 ngày, muốn phòng cao cấp, ăn ngon và tham quan hết.",
            ("khó khả thi", "280.000 VND/người/ngày", "không tự gán giá"),
        ),
        (
            "Chuyến Phú Quốc 3 ngày: tối ngày 1 mới tới và sáng ngày 3 phải rời đi, đừng nhồi lịch.",
            ("Ngày 1 đến muộn", "Ngày 2", "Ngày 3 rời đi sớm"),
        ),
        (
            "Ngày tới TP. Hồ Chí Minh có chắc chợ Bến Thành mở và không mưa không?",
            ("chưa kết nối", "không khẳng định", "kiểm tra"),
        ),
        (
            "Mình phân vân Huế với Hạ Long, mục tiêu chính là văn hóa. Chọn phương án nào?",
            ("chọn Huế", "Hạ Long", "văn hóa"),
        ),
    ],
)
def test_reasoning_policy_is_grounded_and_does_not_call_model(
    message: str, expected_terms: tuple[str, ...]
) -> None:
    model = CapturingChatModel("không nên được gọi")
    response = ChatService(model, "local").chat(ChatRequest(message=message))

    assert all(term in response.reply for term in expected_terms)
    assert model.messages == []
