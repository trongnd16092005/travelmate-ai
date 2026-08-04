import json
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.clients.llm.base import ChatModel
from app.prompts.itinerary import ITINERARY_SYSTEM_PROMPT
from app.schemas.itinerary import (
    BudgetBreakdown,
    ItineraryDay,
    ItineraryPlan,
    ItineraryRequest,
    ItineraryResponse,
    MissingItineraryField,
)
from app.services.chat import get_chat_service


class ItineraryGenerationError(RuntimeError):
    """Raised when the model response cannot be converted to a safe itinerary."""


def _to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


class GeneratedPlan(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    summary: str = Field(min_length=1, max_length=500)
    assumptions: list[str] = Field(default_factory=list, max_length=8)
    days: list[ItineraryDay]


QUESTION_BY_FIELD: dict[MissingItineraryField, str] = {
    "destination": "Bạn muốn đi đâu?",
    "durationDays": "Bạn muốn đi trong bao nhiêu ngày hoặc từ ngày nào đến ngày nào?",
    "numPeople": "Chuyến đi có bao nhiêu người?",
    "budgetVnd": "Tổng ngân sách dự kiến của bạn là bao nhiêu?",
}


def find_missing_fields(request: ItineraryRequest) -> list[MissingItineraryField]:
    missing: list[MissingItineraryField] = []
    if not request.destination or not request.destination.strip():
        missing.append("destination")
    if request.resolved_duration_days() is None:
        missing.append("durationDays")
    if request.num_people is None:
        missing.append("numPeople")
    if request.budget_vnd is None:
        missing.append("budgetVnd")
    return missing


def allocate_budget(total_vnd: int) -> BudgetBreakdown:
    accommodation = total_vnd * 35 // 100
    food = total_vnd * 25 // 100
    transport = total_vnd * 20 // 100
    activities = total_vnd * 15 // 100
    reserve = total_vnd - accommodation - food - transport - activities
    return BudgetBreakdown(
        accommodationVnd=accommodation,
        foodVnd=food,
        transportVnd=transport,
        activitiesVnd=activities,
        reserveVnd=reserve,
        totalVnd=total_vnd,
    )


def extract_json_object(raw_reply: str) -> dict[str, Any]:
    text = raw_reply.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ItineraryGenerationError("AI không trả về JSON lịch trình.")
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ItineraryGenerationError("JSON lịch trình từ AI không hợp lệ.") from exc
    if not isinstance(value, dict):
        raise ItineraryGenerationError("AI phải trả về một JSON object.")
    return value


class ItineraryService:
    def __init__(self, model: ChatModel, provider: str) -> None:
        self.model = model
        self.provider = provider

    def generate(self, request: ItineraryRequest) -> ItineraryResponse:
        missing_fields = find_missing_fields(request)
        if missing_fields:
            return ItineraryResponse(
                status="needs_clarification",
                missingFields=missing_fields,
                questions=[QUESTION_BY_FIELD[field] for field in missing_fields],
            )

        duration_days = request.resolved_duration_days()
        destination = request.destination.strip() if request.destination else ""
        if duration_days is None or request.num_people is None or request.budget_vnd is None:
            raise ItineraryGenerationError("Không thể xác định đủ tham số lịch trình.")

        raw_reply = self.model.generate(
            [
                {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(request, duration_days)},
            ]
        )
        try:
            generated = GeneratedPlan.model_validate(extract_json_object(raw_reply))
        except ValidationError as exc:
            raise ItineraryGenerationError("Cấu trúc lịch trình từ AI không hợp lệ.") from exc

        expected_days = list(range(1, duration_days + 1))
        actual_days = [day.day for day in generated.days]
        if actual_days != expected_days:
            raise ItineraryGenerationError(
                f"AI phải trả đủ các ngày theo thứ tự 1 đến {duration_days}."
            )

        plan = ItineraryPlan(
            destination=destination,
            durationDays=duration_days,
            numPeople=request.num_people,
            summary=generated.summary,
            assumptions=generated.assumptions,
            days=generated.days,
            budget=allocate_budget(request.budget_vnd),
        )
        return ItineraryResponse(status="ready", plan=plan, provider=self.provider)

    @staticmethod
    def _build_user_prompt(request: ItineraryRequest, duration_days: int) -> str:
        preferences = ", ".join(item.strip() for item in request.preferences if item.strip())
        details = [
            f"Điểm đến: {request.destination}",
            f"Số ngày: {duration_days}",
            f"Số người: {request.num_people}",
            f"Tổng ngân sách: {request.budget_vnd:,} VND",
            f"Sở thích: {preferences or 'chưa cung cấp'}",
        ]
        if request.start_date:
            details.append(f"Ngày bắt đầu: {request.start_date.isoformat()}")
        if request.end_date:
            details.append(f"Ngày kết thúc: {request.end_date.isoformat()}")
        if request.notes:
            details.append(f"Lưu ý: {request.notes.strip()}")
        details.append(f"Hãy trả đúng {duration_days} ngày, đánh số liên tục từ 1.")
        return "\n".join(details)


@lru_cache
def get_itinerary_service() -> ItineraryService:
    chat_service = get_chat_service()
    return ItineraryService(chat_service.model, chat_service.provider)
