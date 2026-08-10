import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes.place_suggestions import get_place_suggestion_service
from app.main import app
from app.retrieval.places import NominatimPlaceLocationProvider, PlaceLocation
from app.schemas.place import SuggestPlacesRequest
from app.services.place_suggestions import PlaceSuggestionService


class FakeLocationProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def geocode(self, place_name: str, destination_name: str) -> PlaceLocation:
        self.calls.append((place_name, destination_name))
        return PlaceLocation(
            display_name=f"{place_name}, {destination_name}, Việt Nam",
            latitude=16.0544 + len(self.calls) / 100,
            longitude=108.2022 + len(self.calls) / 100,
            map_url="https://www.openstreetmap.org/search?query=demo",
        )


def test_place_provider_geocodes_and_caches() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json=[
                {
                    "display_name": "bán đảo Sơn Trà, Đà Nẵng, Việt Nam",
                    "lat": "16.1180",
                    "lon": "108.2770",
                }
            ],
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = NominatimPlaceLocationProvider(client=client)

    first = provider.geocode("bán đảo Sơn Trà", "Đà Nẵng")
    second = provider.geocode("bán đảo Sơn Trà", "Đà Nẵng")

    assert first == second
    assert first is not None
    assert first.latitude == 16.118
    assert len(requests) == 1


def test_suggestions_use_catalog_and_do_not_include_ticket_price() -> None:
    provider = FakeLocationProvider()
    response = PlaceSuggestionService(provider).suggest(
        SuggestPlacesRequest(city="Đà Nẵng", count=3)
    )

    assert response.city == "Đà Nẵng"
    assert len(response.suggestions) == 3
    assert provider.calls[0][1] == "Đà Nẵng"
    payload = response.model_dump(by_alias=True)
    assert all("estimatedCostVnd" not in suggestion for suggestion in payload["suggestions"])


def test_hot_destination_can_return_six_map_suggestions() -> None:
    response = PlaceSuggestionService(FakeLocationProvider()).suggest(
        SuggestPlacesRequest(city="Hà Nội", count=6)
    )

    assert len(response.suggestions) == 6
    assert response.suggestions[-1].name == "Hồ Tây"


@pytest.mark.asyncio
async def test_suggest_places_endpoint_returns_map_coordinates() -> None:
    service = PlaceSuggestionService(FakeLocationProvider())
    app.dependency_overrides[get_place_suggestion_service] = lambda: service
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/internal/v1/ai/suggest-places",
                json={"city": "Huế", "count": 2, "specialNote": "đi cùng gia đình"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "catalog"
    assert len(body["suggestions"]) == 2
    assert body["suggestions"][0]["source"] == "OpenStreetMap Nominatim"
    assert isinstance(body["suggestions"][0]["latitude"], float)
