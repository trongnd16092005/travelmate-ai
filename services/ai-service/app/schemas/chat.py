from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChatHistoryMessage(ApiModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class TripContext(ApiModel):
    destination: str | None = Field(default=None, min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    budget_vnd: int | None = Field(default=None, ge=0)
    num_people: int | None = Field(default=None, ge=1, le=50)


class ChatRequest(ApiModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=10)
    trip_context: TripContext | None = None


class ChatResponse(ApiModel):
    reply: str
    is_out_of_scope: bool
    suggested_questions: list[str] = Field(default_factory=list, max_length=3)
    provider: Literal["mock", "gemini", "local"]
