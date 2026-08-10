from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from time import monotonic
from typing import Protocol

import httpx


@dataclass(frozen=True)
class WeatherSnapshot:
    location_name: str
    observed_at: str
    temperature_c: float
    apparent_temperature_c: float
    precipitation_mm: float
    wind_speed_kmh: float
    weather_code: int
    daily_precipitation_probability_max: int | None
    retrieved_at: datetime
    source_name: str = "Open-Meteo Weather Forecast API"
    source_url: str = "https://open-meteo.com/en/docs"


class WeatherProvider(Protocol):
    def get_current(self, destination_name: str) -> WeatherSnapshot | None:
        """Return source-backed current conditions, or None when unavailable."""


@dataclass(frozen=True)
class _CacheEntry:
    expires_at: float
    snapshot: WeatherSnapshot


class OpenMeteoWeatherProvider:
    def __init__(
        self,
        *,
        timeout_seconds: float = 5.0,
        cache_ttl_seconds: int = 900,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, _CacheEntry] = {}
        self._lock = Lock()

    def get_current(self, destination_name: str) -> WeatherSnapshot | None:
        cache_key = destination_name.casefold().strip()
        now = monotonic()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None and cached.expires_at > now:
                return cached.snapshot

        try:
            location = self._geocode(destination_name)
            if location is None:
                return None
            snapshot = self._forecast(location)
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return None

        with self._lock:
            self._cache[cache_key] = _CacheEntry(
                expires_at=now + self._cache_ttl_seconds,
                snapshot=snapshot,
            )
        return snapshot

    def _geocode(self, destination_name: str) -> dict[str, object] | None:
        response = self._client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": destination_name,
                "count": 5,
                "language": "vi",
                "format": "json",
                "countryCode": "VN",
            },
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        return next(
            (result for result in results if result.get("country_code") == "VN"),
            None,
        )

    def _forecast(self, location: dict[str, object]) -> WeatherSnapshot:
        response = self._client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": (
                    "temperature_2m,apparent_temperature,precipitation,"
                    "weather_code,wind_speed_10m"
                ),
                "daily": "precipitation_probability_max",
                "forecast_days": 1,
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        payload = response.json()
        current = payload["current"]
        daily_values = payload.get("daily", {}).get("precipitation_probability_max") or []
        probability = daily_values[0] if daily_values else None
        return WeatherSnapshot(
            location_name=str(location.get("name") or "điểm đến"),
            observed_at=str(current["time"]),
            temperature_c=float(current["temperature_2m"]),
            apparent_temperature_c=float(current["apparent_temperature"]),
            precipitation_mm=float(current["precipitation"]),
            wind_speed_kmh=float(current["wind_speed_10m"]),
            weather_code=int(current["weather_code"]),
            daily_precipitation_probability_max=(
                int(probability) if probability is not None else None
            ),
            retrieved_at=datetime.now(UTC),
        )


WEATHER_CODE_LABELS: dict[int, str] = {
    0: "trời quang",
    1: "chủ yếu quang",
    2: "có mây rải rác",
    3: "nhiều mây",
    45: "có sương mù",
    48: "có sương mù đóng băng",
    51: "mưa phùn nhẹ",
    53: "mưa phùn vừa",
    55: "mưa phùn dày",
    61: "mưa nhẹ",
    63: "mưa vừa",
    65: "mưa lớn",
    71: "tuyết nhẹ",
    73: "tuyết vừa",
    75: "tuyết dày",
    80: "mưa rào nhẹ",
    81: "mưa rào vừa",
    82: "mưa rào mạnh",
    95: "có dông",
    96: "dông kèm mưa đá nhẹ",
    99: "dông kèm mưa đá mạnh",
}


def describe_weather_code(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, f"mã thời tiết WMO {code}")
