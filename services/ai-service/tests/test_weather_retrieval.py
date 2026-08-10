from datetime import UTC, datetime

import httpx

from app.clients.llm.base import ChatMessage
from app.retrieval.weather import OpenMeteoWeatherProvider, WeatherSnapshot
from app.schemas.chat import ChatRequest
from app.services.chat import ChatService


class NeverCalledModel:
    def __init__(self) -> None:
        self.messages: list[ChatMessage] = []

    def generate(self, messages: list[ChatMessage]) -> str:
        self.messages = messages
        return "không nên được gọi"


class FakeWeatherProvider:
    def __init__(self, snapshot: WeatherSnapshot | None) -> None:
        self.snapshot = snapshot
        self.calls: list[str] = []

    def get_current(self, destination_name: str) -> WeatherSnapshot | None:
        self.calls.append(destination_name)
        return self.snapshot


def _snapshot() -> WeatherSnapshot:
    return WeatherSnapshot(
        location_name="Cao Bằng",
        observed_at="2026-08-10T14:15",
        temperature_c=28.5,
        apparent_temperature_c=30.0,
        precipitation_mm=0.2,
        wind_speed_kmh=8.4,
        weather_code=61,
        daily_precipitation_probability_max=65,
        retrieved_at=datetime(2026, 8, 10, 7, 16, tzinfo=UTC),
    )


def test_open_meteo_provider_geocodes_fetches_and_caches() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "geocoding-api.open-meteo.com":
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Cao Bằng",
                            "country_code": "VN",
                            "latitude": 22.67,
                            "longitude": 106.25,
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "current": {
                    "time": "2026-08-10T14:15",
                    "temperature_2m": 28.5,
                    "apparent_temperature": 30.0,
                    "precipitation": 0.2,
                    "weather_code": 61,
                    "wind_speed_10m": 8.4,
                },
                "daily": {"precipitation_probability_max": [65]},
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenMeteoWeatherProvider(client=client, cache_ttl_seconds=900)

    first = provider.get_current("Cao Bằng")
    second = provider.get_current("Cao Bằng")

    assert first == second
    assert first is not None
    assert first.weather_code == 61
    assert first.daily_precipitation_probability_max == 65
    assert len(requests) == 2


def test_open_meteo_provider_fails_closed() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(503))
    )
    provider = OpenMeteoWeatherProvider(client=client)

    assert provider.get_current("Cao Bằng") is None


def test_chat_returns_compact_weather_without_exposing_provider_metadata() -> None:
    model = NeverCalledModel()
    weather = FakeWeatherProvider(_snapshot())
    service = ChatService(model, "local", weather_provider=weather)

    response = service.chat(ChatRequest(message="Thời tiết Cao Bằng hiện tại thế nào?"))

    assert "28.5°C" in response.reply
    assert "Xác suất mưa" in response.reply
    assert "Open-Meteo Weather Forecast API" not in response.reply
    assert "https://open-meteo.com/en/docs" not in response.reply
    assert "2026-08-10 07:16 UTC" not in response.reply
    assert "Nguồn:" not in response.reply
    assert "Thông tin có thể thay đổi" in response.reply
    assert weather.calls == ["Cao Bằng"]
    assert model.messages == []


def test_chat_does_not_guess_when_realtime_source_is_unavailable() -> None:
    model = NeverCalledModel()
    weather = FakeWeatherProvider(None)
    service = ChatService(model, "local", weather_provider=weather)

    response = service.chat(ChatRequest(message="Đà Nẵng có mưa không?"))

    assert "không dùng dữ liệu cũ hoặc tự đoán" in response.reply
    assert model.messages == []


def test_weather_safety_guardrail_runs_before_retrieval() -> None:
    model = NeverCalledModel()
    weather = FakeWeatherProvider(_snapshot())
    service = ChatService(model, "local", weather_provider=weather)

    response = service.chat(
        ChatRequest(message="Cao Bằng đang mưa lớn nhưng tôi vẫn muốn qua đèo")
    )

    assert "không nên tiếp tục" in response.reply
    assert weather.calls == []
    assert model.messages == []
