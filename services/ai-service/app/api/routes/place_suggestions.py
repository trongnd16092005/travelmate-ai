from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from app.schemas.place import PlaceSuggestionResponse, SuggestPlacesRequest
from app.services.place_suggestions import (
    PlaceSuggestionService,
    get_place_suggestion_service,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/suggest-places", response_model=PlaceSuggestionResponse)
async def suggest_places(
    request: SuggestPlacesRequest,
    service: Annotated[PlaceSuggestionService, Depends(get_place_suggestion_service)],
) -> PlaceSuggestionResponse:
    return await run_in_threadpool(service.suggest, request)
