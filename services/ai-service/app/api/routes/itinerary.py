from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from app.clients.llm.base import ChatModelUnavailableError
from app.schemas.itinerary import ItineraryRequest, ItineraryResponse
from app.services.itinerary import (
    ItineraryGenerationError,
    ItineraryService,
    get_itinerary_service,
)

router = APIRouter(prefix="/ai/itineraries", tags=["ai"])


@router.post("/generate", response_model=ItineraryResponse)
async def generate_itinerary(
    request: ItineraryRequest,
    service: Annotated[ItineraryService, Depends(get_itinerary_service)],
) -> ItineraryResponse:
    try:
        return await run_in_threadpool(service.generate, request)
    except ChatModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ItineraryGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
