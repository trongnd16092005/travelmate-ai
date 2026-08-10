import pytest

from app.clients.llm.base import ChatMessage
from app.knowledge.destinations import NATIONWIDE_DESTINATIONS
from app.schemas.chat import ChatRequest
from app.services.chat import ChatService


class HallucinatingChatModel:
    def __init__(self) -> None:
        self.messages: list[ChatMessage] = []

    def generate(self, messages: list[ChatMessage]) -> str:
        self.messages = messages
        return "Hãy ghé Công viên Mây Trắng và Bảo tàng Mặt Trời."


@pytest.mark.parametrize("destination", NATIONWIDE_DESTINATIONS)
def test_place_recommendations_are_grounded_for_all_current_provinces(destination) -> None:
    model = HallucinatingChatModel()
    response = ChatService(model, "local").chat(
        ChatRequest(message=f"Gợi ý ba điểm tham quan ở {destination.name}")
    )

    assert destination.name in response.reply
    assert all(place.name in response.reply for place in destination.places)
    assert "Mây Trắng" not in response.reply
    assert model.messages == []


@pytest.mark.parametrize(
    ("legacy_name", "current_name"),
    [
        ("Hà Giang", "Tuyên Quang"),
        ("Quảng Bình", "Quảng Trị"),
        ("Bến Tre", "Vĩnh Long"),
        ("Bạc Liêu", "Cà Mau"),
        ("Phú Quốc", "An Giang"),
    ],
)
def test_legacy_alias_recommendations_use_current_province(
    legacy_name: str,
    current_name: str,
) -> None:
    model = HallucinatingChatModel()
    response = ChatService(model, "local").chat(
        ChatRequest(message=f"Nên đi đâu ở {legacy_name}?")
    )

    assert current_name in response.reply
    assert model.messages == []


def test_food_recommendation_only_uses_retrieved_catalog() -> None:
    model = HallucinatingChatModel()
    destination = next(item for item in NATIONWIDE_DESTINATIONS if item.name == "Cao Bằng")

    response = ChatService(model, "local").chat(
        ChatRequest(message="Cao Bằng có đặc sản gì và nên tham quan đâu?")
    )

    assert all(place.name in response.reply for place in destination.places)
    assert all(food in response.reply for food in destination.foods)
    assert model.messages == []


def test_non_factual_model_turn_receives_grounded_catalog_context() -> None:
    model = HallucinatingChatModel()
    service = ChatService(model, "local")
    messages = service.build_messages(
        ChatRequest(message="Tư vấn thêm cho chuyến đi Cao Bằng")
    )

    catalog_context = next(
        message["content"]
        for message in messages
        if message["role"] == "system" and "[GROUNDED_CATALOG]" in message["content"]
    )
    assert "Tỉnh/thành hiện hành: Cao Bằng" in catalog_context
    assert "thác Bản Giốc" in catalog_context
    assert "Không tạo thêm tên địa điểm" in catalog_context


def test_validator_replaces_unknown_place_from_free_model_reply() -> None:
    model = HallucinatingChatModel()
    request = ChatRequest.model_validate(
        {
            "message": "Tư vấn tiếp giúp mình",
            "history": [
                {"role": "user", "content": "Mình muốn đi Cao Bằng"},
                {"role": "assistant", "content": "Mình đã ghi nhận."},
            ],
        }
    )

    response = ChatService(model, "local").chat(request)

    assert "Mây Trắng" not in response.reply
    assert "thác Bản Giốc" in response.reply
    assert model.messages
