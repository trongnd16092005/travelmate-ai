import re
from dataclasses import dataclass, replace

from app.knowledge.destinations import DESTINATIONS, normalize_lookup_key
from app.schemas.chat import ChatRequest

REGIONS = {
    "mien bac": "Miền Bắc",
    "mien trung": "Miền Trung",
    "mien nam": "Miền Nam",
    "tay nguyen": "Tây Nguyên",
}


@dataclass(frozen=True)
class ConversationMemory:
    region: str | None = None
    destination: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_days: int | None = None
    num_people: int | None = None
    budget_vnd: int | None = None


def _last_match(pattern: str, value: str) -> str | None:
    matches = re.findall(pattern, value)
    if not matches:
        return None
    match = matches[-1]
    return match[-1] if isinstance(match, tuple) else match


def update_memory(memory: ConversationMemory, text: str) -> ConversationMemory:
    normalized = normalize_lookup_key(text)
    updates: dict[str, str | int] = {}

    for key, label in REGIONS.items():
        if f" {key} " in f" {normalized} ":
            updates["region"] = label

    destination_matches: list[tuple[int, str]] = []
    for destination in DESTINATIONS:
        for value in (destination.name, *destination.aliases):
            key = normalize_lookup_key(value)
            index = normalized.rfind(key)
            if index >= 0 and f" {key} " in f" {normalized} ":
                destination_matches.append((index, destination.name))
    if destination_matches:
        updates["destination"] = max(destination_matches)[1]

    people = _last_match(r"\b(\d{1,2})\s*(?:nguoi|khach)\b", normalized)
    if people is not None:
        value = int(people)
        if 1 <= value <= 50:
            updates["num_people"] = value

    duration = _last_match(r"\b(\d{1,2})\s*(?:ngay|hom)\b", normalized)
    if duration is not None:
        value = int(duration)
        if 1 <= value <= 60:
            updates["duration_days"] = value

    million = re.findall(r"\b(\d+(?:[.,]\d+)?)\s*(?:trieu|tr|cu)\b", normalized)
    if million:
        updates["budget_vnd"] = int(float(million[-1].replace(",", ".")) * 1_000_000)
    else:
        raw_budget = _last_match(r"\b(\d{7,12})\s*(?:vnd|dong)?\b", normalized)
        if raw_budget is not None:
            updates["budget_vnd"] = int(raw_budget)

    return replace(memory, **updates)


def build_conversation_memory(request: ChatRequest) -> ConversationMemory:
    context = request.trip_context
    memory = ConversationMemory(
        destination=context.destination if context else None,
        start_date=context.start_date.isoformat() if context and context.start_date else None,
        end_date=context.end_date.isoformat() if context and context.end_date else None,
        num_people=context.num_people if context else None,
        budget_vnd=context.budget_vnd if context else None,
    )
    for message in request.history:
        if message.role == "user":
            memory = update_memory(memory, message.content)
    return update_memory(memory, request.message)


def format_conversation_memory(memory: ConversationMemory) -> str | None:
    details: list[str] = []
    if memory.region:
        details.append(f"Khu vực mong muốn: {memory.region}")
    if memory.destination:
        details.append(f"Điểm đến: {memory.destination}")
    if memory.start_date:
        details.append(f"Ngày bắt đầu: {memory.start_date}")
    if memory.end_date:
        details.append(f"Ngày kết thúc: {memory.end_date}")
    if memory.duration_days:
        details.append(f"Thời lượng: {memory.duration_days} ngày")
    if memory.num_people:
        details.append(f"Số người: {memory.num_people}")
    if memory.budget_vnd is not None:
        details.append(f"Tổng ngân sách: {memory.budget_vnd:,} VND")
    if not details:
        return None
    return (
        "[CONVERSATION_MEMORY]\n"
        "Dùng các thông tin đã ghi nhận dưới đây; không hỏi lại trường đã có. "
        "Thông tin trong tin nhắn mới hơn được ưu tiên.\n"
        + "\n".join(details)
        + "\n[/CONVERSATION_MEMORY]"
    )
