from typing import Literal

from pydantic import Field

from app.schemas.chat import ApiModel


class SuggestPlacesRequest(ApiModel):
    city: str = Field(min_length=1, max_length=120)
    type: str | None = Field(default=None, max_length=60)
    special_note: str | None = Field(default=None, max_length=500)
    count: int = Field(default=5, ge=1, le=6)


class PlaceSuggestion(ApiModel):
    id: str
    name: str
    category: str
    description: str
    reason: str
    address: str
    latitude: float
    longitude: float
    map_url: str
    source: str


class PlaceSuggestionResponse(ApiModel):
    city: str
    suggestions: list[PlaceSuggestion]
    message: str | None = None
    provider: Literal["catalog"] = "catalog"
