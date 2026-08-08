import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes.itinerary import get_itinerary_service
from app.clients.llm.base import ChatMessage
from app.clients.llm.mock import MockChatModel
from app.main import app
from app.schemas.itinerary import ItineraryRequest
from app.services.itinerary import ItineraryService, allocate_budget


class StructuredItineraryModel:
    def __init__(self, reply: str | None = None) -> None:
        self.messages: list[ChatMessage] = []
        self.reply = reply or json.dumps(
            {
                "days": [
                    {
                        "day": day,
                        "activities": [
                            {
                                "period": "morning",
                                "kind": "visit",
                                "placeId": "da-nang:ban-dao-son-tra",
                            }
                        ],
                    }
                    for day in range(1, 4)
                ],
            },
            ensure_ascii=False,
        )

    def generate(self, messages: list[ChatMessage]) -> str:
        self.messages = messages
        return self.reply


def test_missing_fields_are_deterministic_and_do_not_call_model() -> None:
    model = StructuredItineraryModel()
    service = ItineraryService(model, "local")

    response = service.generate(ItineraryRequest(destination="Đà Nẵng"))

    assert response.status == "needs_clarification"
    assert response.missing_fields == ["durationDays", "numPeople", "budgetVnd"]
    assert len(response.questions) == 3
    assert model.messages == []


def test_budget_allocation_always_matches_requested_total() -> None:
    budget = allocate_budget(5_000_003)

    allocated = (
        budget.accommodation_vnd
        + budget.food_vnd
        + budget.transport_vnd
        + budget.activities_vnd
        + budget.reserve_vnd
    )
    assert allocated == budget.total_vnd == 5_000_003


def test_ready_itinerary_uses_model_content_and_backend_budget() -> None:
    model = StructuredItineraryModel()
    service = ItineraryService(model, "local")
    request = ItineraryRequest(
        destination="Đà Nẵng",
        durationDays=3,
        numPeople=2,
        budgetVnd=5_000_000,
        preferences=["biển", "ẩm thực"],
    )

    response = service.generate(request)

    assert response.status == "ready"
    assert response.provider == "local"
    assert response.plan is not None
    assert len(response.plan.days) == 3
    assert response.plan.budget.total_vnd == 5_000_000
    assert response.plan.days[0].activities[0].place_name == "bán đảo Sơn Trà"
    assert "Sở thích: biển, ẩm thực" in model.messages[-1]["content"]
    assert "da-nang:ban-dao-son-tra" in model.messages[-1]["content"]


def test_itinerary_rejects_place_id_outside_destination_catalog() -> None:
    reply = json.dumps(
        {
            "days": [
                {
                    "day": 1,
                    "activities": [
                        {
                            "period": "morning",
                            "kind": "visit",
                            "placeId": "quy-nhon:ky-co",
                        }
                    ],
                }
            ]
        }
    )
    service = ItineraryService(StructuredItineraryModel(reply), "local")

    with pytest.raises(RuntimeError, match="không thuộc danh mục"):
        service.generate(
            ItineraryRequest(
                destination="Đà Nẵng",
                durationDays=1,
                numPeople=2,
                budgetVnd=2_000_000,
            )
        )


def test_itinerary_normalizes_destination_alias_and_grounded_title() -> None:
    reply = json.dumps(
        {
            "days": [
                {
                    "day": 1,
                    "activities": [
                        {
                            "period": "morning",
                            "kind": "visit",
                            "placeId": "tp-ho-chi-minh:cho-ben-thanh",
                        }
                    ],
                }
            ]
        }
    )
    service = ItineraryService(StructuredItineraryModel(reply), "local")

    response = service.generate(
        ItineraryRequest(
            destination="Sài Gòn",
            durationDays=1,
            numPeople=2,
            budgetVnd=2_000_000,
        )
    )

    assert response.plan is not None
    assert response.plan.destination == "TP. Hồ Chí Minh"
    assert response.plan.days[0].activities[0].title == "Tham quan chợ Bến Thành"


def test_mock_model_supports_structured_itinerary_demo() -> None:
    service = ItineraryService(MockChatModel(), "mock")

    response = service.generate(
        ItineraryRequest(
            destination="Huế",
            durationDays=2,
            numPeople=2,
            budgetVnd=3_000_000,
        )
    )

    assert response.status == "ready"
    assert response.plan is not None
    assert len(response.plan.days) == 2
    assert response.plan.budget.total_vnd == 3_000_000


@pytest.mark.asyncio
async def test_itinerary_endpoint_returns_clarification_without_loading_model() -> None:
    model = StructuredItineraryModel()
    app.dependency_overrides[get_itinerary_service] = lambda: ItineraryService(model, "mock")
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/internal/v1/ai/itineraries/generate",
                json={"destination": "Huế"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_clarification"
    assert body["missingFields"] == ["durationDays", "numPeople", "budgetVnd"]
    assert body["plan"] is None


@pytest.mark.asyncio
async def test_itinerary_endpoint_returns_structured_plan() -> None:
    model = StructuredItineraryModel()
    app.dependency_overrides[get_itinerary_service] = lambda: ItineraryService(model, "mock")
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/internal/v1/ai/itineraries/generate",
                json={
                    "destination": "Đà Nẵng",
                    "durationDays": 3,
                    "numPeople": 2,
                    "budgetVnd": 5_000_000,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["plan"]["budget"]["totalVnd"] == 5_000_000
    assert len(body["plan"]["days"]) == 3
