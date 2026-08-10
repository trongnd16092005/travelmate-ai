from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Protocol
from urllib.parse import quote

import httpx


@dataclass(frozen=True)
class PlaceLocation:
    display_name: str
    latitude: float
    longitude: float
    map_url: str
    source_name: str = "OpenStreetMap Nominatim"


class PlaceLocationProvider(Protocol):
    def geocode(self, place_name: str, destination_name: str) -> PlaceLocation | None:
        """Resolve a catalog place to source-backed coordinates."""


@dataclass(frozen=True)
class _CacheEntry:
    expires_at: float
    location: PlaceLocation | None


class NominatimPlaceLocationProvider:
    def __init__(
        self,
        *,
        timeout_seconds: float = 5.0,
        cache_ttl_seconds: int = 86_400,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(
            timeout=timeout_seconds,
            headers={"User-Agent": "TravelMate/1.0 (local educational demo)"},
        )
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, _CacheEntry] = {}
        self._lock = Lock()

    def geocode(self, place_name: str, destination_name: str) -> PlaceLocation | None:
        cache_key = f"{place_name}|{destination_name}".casefold().strip()
        now = monotonic()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None and cached.expires_at > now:
                return cached.location

        try:
            response = self._client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{place_name}, {destination_name}, Việt Nam",
                    "format": "jsonv2",
                    "limit": 1,
                    "countrycodes": "vn",
                    "accept-language": "vi",
                },
            )
            response.raise_for_status()
            results = response.json()
            location = self._to_location(results[0]) if results else None
        except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError):
            location = None

        with self._lock:
            self._cache[cache_key] = _CacheEntry(
                expires_at=now + self._cache_ttl_seconds,
                location=location,
            )
        return location

    @staticmethod
    def _to_location(result: dict[str, object]) -> PlaceLocation:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
        return PlaceLocation(
            display_name=str(result.get("display_name") or "Việt Nam"),
            latitude=latitude,
            longitude=longitude,
            map_url=(
                "https://www.openstreetmap.org/search?query="
                + quote(str(result.get("display_name") or f"{latitude},{longitude}"))
            ),
        )
