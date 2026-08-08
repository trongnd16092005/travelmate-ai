import json
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.clients.llm.base import ChatModel
from app.knowledge.destinations import DestinationKnowledge, resolve_destination
from app.prompts.itinerary import ITINERARY_SYSTEM_PROMPT
from app.schemas.itinerary import (
    BudgetBreakdown,
    ItineraryActivity,
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


class GeneratedActivity(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    period: str
    kind: str
    place_id: str | None = None


class GeneratedDay(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    day: int = Field(ge=1, le=14)
    activities: list[GeneratedActivity] = Field(min_length=1, max_length=3)


class GeneratedPlan(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    days: list[GeneratedDay]


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

        destination_knowledge = resolve_destination(destination)
        raw_reply = self.model.generate(
            [
                {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": self._build_user_prompt(
                        request,
                        duration_days,
                        destination_knowledge,
                    ),
                },
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

        grounded_days = self._ground_days(generated.days, destination_knowledge)
        canonical_destination = (
            destination_knowledge.name if destination_knowledge is not None else destination
        )
        assumptions = [
            "Kiểm tra thời tiết, giờ hoạt động và tình trạng dịch vụ trước khi đi."
        ]
        if destination_knowledge is not None:
            assumptions.append("Địa điểm được giới hạn theo danh mục TravelMate.")
        else:
            assumptions.append(
                "TravelMate chưa có danh mục địa điểm cho điểm đến này; lịch chỉ gồm hoạt động chung."
            )
        plan = ItineraryPlan(
            destination=canonical_destination,
            durationDays=duration_days,
            numPeople=request.num_people,
            summary=f"Lịch trình {duration_days} ngày tại {canonical_destination}.",
            assumptions=assumptions,
            days=grounded_days,
            budget=allocate_budget(request.budget_vnd),
        )
        return ItineraryResponse(status="ready", plan=plan, provider=self.provider)

    @staticmethod
    def _build_user_prompt(
        request: ItineraryRequest,
        duration_days: int,
        destination_knowledge: DestinationKnowledge | None,
    ) -> str:
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
        if destination_knowledge is not None:
            details.append("Danh sách placeId được phép:")
            details.extend(
                f"- {place.id} | {place.name}" for place in destination_knowledge.places
            )
        else:
            details.append(
                "Danh mục chưa hỗ trợ điểm đến này: không dùng hoạt động visit và mọi placeId phải null."
            )
        details.append(f"Hãy trả đúng {duration_days} ngày, đánh số liên tục từ 1.")
        return "\n".join(details)

    @staticmethod
    def _ground_days(
        generated_days: list[GeneratedDay],
        destination: DestinationKnowledge | None,
    ) -> list[ItineraryDay]:
        allowed_periods = {"morning", "afternoon", "evening"}
        allowed_kinds = {"visit", "meal", "rest", "travel", "free_time"}
        kind_titles = {
            "meal": "Trải nghiệm ẩm thực địa phương",
            "rest": "Nghỉ ngơi",
            "travel": "Di chuyển",
            "free_time": "Thời gian tự do",
        }
        place_by_id = destination.place_by_id if destination is not None else {}
        grounded_days: list[ItineraryDay] = []
        grounded_visits = 0

        for day in generated_days:
            periods: set[str] = set()
            activities: list[ItineraryActivity] = []
            for activity in day.activities:
                if activity.period not in allowed_periods:
                    raise ItineraryGenerationError("AI trả về buổi hoạt động không hợp lệ.")
                if activity.period in periods:
                    raise ItineraryGenerationError("Mỗi ngày chỉ được có một hoạt động cho mỗi buổi.")
                periods.add(activity.period)
                if activity.kind not in allowed_kinds:
                    raise ItineraryGenerationError("AI trả về loại hoạt động không hợp lệ.")

                if activity.kind == "visit":
                    if not activity.place_id or activity.place_id not in place_by_id:
                        raise ItineraryGenerationError(
                            "AI chọn địa điểm không thuộc danh mục của điểm đến."
                        )
                    place = place_by_id[activity.place_id]
                    grounded_visits += 1
                    title = f"Tham quan {place.name}"
                    place_name = place.name
                else:
                    if activity.place_id is not None:
                        raise ItineraryGenerationError(
                            "Chỉ hoạt động visit mới được gắn placeId."
                        )
                    title = kind_titles[activity.kind]
                    place_name = None

                activities.append(
                    ItineraryActivity(
                        period=activity.period,
                        title=title,
                        placeName=place_name,
                        notes=None,
                    )
                )

            day_destination = destination.name if destination is not None else "điểm đến"
            grounded_days.append(
                ItineraryDay(
                    day=day.day,
                    title=f"Ngày {day.day} tại {day_destination}",
                    activities=activities,
                )
            )

        if destination is not None and grounded_visits == 0:
            raise ItineraryGenerationError("Lịch trình phải có ít nhất một địa điểm đã được grounding.")
        return grounded_days


@lru_cache
def get_itinerary_service() -> ItineraryService:
    chat_service = get_chat_service()
    return ItineraryService(chat_service.model, chat_service.provider)
