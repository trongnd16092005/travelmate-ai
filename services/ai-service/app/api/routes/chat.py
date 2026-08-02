from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from app.clients.llm.base import LocalModelUnavailableError
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService, get_chat_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    try:
        return await run_in_threadpool(service.chat, request)
    except LocalModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
