from functools import lru_cache

from app.core.config import settings
from app.knowledge.destinations import resolve_destination
from app.retrieval.places import NominatimPlaceLocationProvider, PlaceLocationProvider
from app.schemas.place import (
    PlaceSuggestion,
    PlaceSuggestionResponse,
    SuggestPlacesRequest,
)


class PlaceSuggestionService:
    def __init__(self, location_provider: PlaceLocationProvider) -> None:
        self._location_provider = location_provider

    def suggest(self, request: SuggestPlacesRequest) -> PlaceSuggestionResponse:
        destination = resolve_destination(request.city)
        if destination is None:
            return PlaceSuggestionResponse(
                city=request.city,
                suggestions=[],
                message="Điểm đến này chưa có trong danh mục địa điểm của TravelMate.",
            )

        suggestions: list[PlaceSuggestion] = []
        for place in destination.places[: request.count]:
            location = self._location_provider.geocode(place.name, destination.name)
            if location is None:
                continue
            suggestions.append(
                PlaceSuggestion(
                    id=place.id,
                    name=place.name,
                    category="ĐỊA ĐIỂM",
                    description=f"Địa điểm trong danh mục TravelMate tại {destination.name}.",
                    reason=(
                        f"Địa điểm nổi bật có thể cân nhắc đưa vào lịch trình "
                        f"tại {destination.name}."
                    ),
                    address=location.display_name,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    mapUrl=location.map_url,
                    source=location.source_name,
                )
            )

        message = None
        if not suggestions:
            message = "Chưa lấy được tọa độ địa điểm từ OpenStreetMap. Vui lòng thử lại."
        return PlaceSuggestionResponse(
            city=destination.name,
            suggestions=suggestions,
            message=message,
        )


@lru_cache
def get_place_suggestion_service() -> PlaceSuggestionService:
    return PlaceSuggestionService(
        NominatimPlaceLocationProvider(
            timeout_seconds=settings.place_geocoding_timeout_seconds,
            cache_ttl_seconds=settings.place_geocoding_cache_ttl_seconds,
        )
    )
