import re
from dataclasses import dataclass, replace

from app.knowledge.destinations import find_destination_mentions, normalize_lookup_key
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
    transport_included: bool | None = None
    pace: str | None = None
    interests: tuple[str, ...] = ()
    last_answered_slot: str | None = None


def _last_match(pattern: str, value: str) -> str | None:
    matches = re.findall(pattern, value)
    if not matches:
        return None
    match = matches[-1]
    return match[-1] if isinstance(match, tuple) else match


def _select_destination(
    normalized: str,
    matches: list[tuple[int, int, str]],
) -> str:
    """Choose the intended target when a correction mentions old and new places."""
    replacement_marker = re.search(r"\b(?:thay cho|thay vi)\b", normalized)
    if replacement_marker:
        before = [match for match in matches if match[1] <= replacement_marker.start()]
        if before:
            return max(before, key=lambda match: match[0])[2]

    source_to_target = re.search(r"\b(?:thay|doi|chuyen)\b.*?\b(?:bang|sang|qua)\b", normalized)
    if source_to_target:
        target_marker = max(
            marker.end()
            for marker in re.finditer(r"\b(?:bang|sang|qua)\b", source_to_target.group())
        ) + source_to_target.start()
        after = [match for match in matches if match[0] >= target_marker]
        if after:
            return min(after, key=lambda match: match[0])[2]

    return max(matches, key=lambda match: match[0])[2]


def infer_pending_slot(text: str) -> str | None:
    normalized = normalize_lookup_key(text)
    if "chi phi di chuyen" in normalized and any(
        term in normalized for term in ("da gom", "bao gom", "gom chi phi")
    ):
        return "transport_included"
    if any(term in normalized for term in ("bao nhieu ngay", "may ngay", "thoi luong")):
        return "duration_days"
    if any(term in normalized for term in ("bao nhieu nguoi", "may nguoi", "bao nhieu khach")):
        return "num_people"
    if "ngan sach" in normalized and any(term in normalized for term in ("bao nhieu", "du kien")):
        return "budget_vnd"
    return None


def update_memory(
    memory: ConversationMemory,
    text: str,
    pending_slot: str | None = None,
) -> ConversationMemory:
    normalized = normalize_lookup_key(text)
    updates: dict[str, object] = {"last_answered_slot": None}

    detected_region: str | None = None
    for key, label in REGIONS.items():
        if f" {key} " in f" {normalized} ":
            detected_region = label
            updates["region"] = label

    destination_matches = [
        (start, end, destination.name)
        for start, end, destination in find_destination_mentions(text)
    ]
    if destination_matches:
        detected_destination = _select_destination(normalized, destination_matches)
        if memory.destination and detected_destination != memory.destination:
            memory = ConversationMemory()
        updates["destination"] = detected_destination
    elif detected_region and memory.destination and any(
        term in normalized
        for term in (
            "muon di",
            "du lich",
            "doi sang",
            "doi qua",
            "chuyen sang",
            "chuyen qua",
            "chuyen moi",
            "chuyen tiep theo",
            "kham pha",
        )
    ):
        memory = ConversationMemory()

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

    if pending_slot == "transport_included":
        if normalized in {"roi", "co", "da gom", "gom roi", "co roi", "bao gom roi"}:
            updates["transport_included"] = True
            updates["last_answered_slot"] = pending_slot
        elif normalized in {"chua", "khong", "chua gom", "khong gom", "chua co"}:
            updates["transport_included"] = False
            updates["last_answered_slot"] = pending_slot

    if pending_slot in {"duration_days", "num_people"}:
        bare_number = re.fullmatch(r"\s*(\d{1,2})\s*", normalized)
        if bare_number:
            value = int(bare_number.group(1))
            if pending_slot == "duration_days" and 1 <= value <= 60:
                updates["duration_days"] = value
                updates["last_answered_slot"] = pending_slot
            elif pending_slot == "num_people" and 1 <= value <= 50:
                updates["num_people"] = value
                updates["last_answered_slot"] = pending_slot

    pace = None
    if any(
        term in normalized
        for term in (
            "khong qua day",
            "khong muon lich day",
            "khong muon lich qua day",
            "thong tha",
            "thu tha",
            "chill",
        )
    ):
        pace = "thư thả"
    elif any(term in normalized for term in ("lich day", "di nhieu noi", "soi dong")):
        pace = "sôi động"
    if pace:
        updates["pace"] = pace

    interests = list(memory.interests)
    interest_terms = {
        "ẩm thực": ("an uong", "am thuc", "mon ngon", "dac san"),
        "biển": ("bien",),
        "văn hóa": ("van hoa", "lich su"),
        "thiên nhiên": ("thien nhien", "canh quan"),
        "nghỉ ngơi": ("nghi ngoi", "thu gian"),
    }
    for label, terms in interest_terms.items():
        if any(term in normalized for term in terms) and label not in interests:
            interests.append(label)
    if interests != list(memory.interests):
        updates["interests"] = tuple(interests)

    return replace(memory, **updates)


def build_conversation_memory(request: ChatRequest) -> ConversationMemory:
    context = request.trip_context
    explicit_destination = None
    for text in [
        *(message.content for message in request.history if message.role == "user"),
        request.message,
    ]:
        candidate = update_memory(ConversationMemory(), text).destination
        if candidate:
            explicit_destination = candidate
    context_matches_destination = not (
        context
        and context.destination
        and explicit_destination
        and context.destination != explicit_destination
    )
    memory = ConversationMemory(
        destination=(
            context.destination if context and context_matches_destination else None
        ),
        start_date=(
            context.start_date.isoformat()
            if context and context.start_date and context_matches_destination
            else None
        ),
        end_date=(
            context.end_date.isoformat()
            if context and context.end_date and context_matches_destination
            else None
        ),
        num_people=context.num_people if context and context_matches_destination else None,
        budget_vnd=context.budget_vnd if context and context_matches_destination else None,
    )
    pending_slot: str | None = None
    for message in request.history:
        if message.role == "assistant":
            pending_slot = infer_pending_slot(message.content)
        else:
            memory = update_memory(memory, message.content, pending_slot)
            pending_slot = None
    return update_memory(memory, request.message, pending_slot)


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
    if memory.transport_included is not None:
        state = "đã bao gồm" if memory.transport_included else "chưa bao gồm"
        details.append(f"Chi phí di chuyển đến điểm đến: {state} trong tổng ngân sách")
    if memory.pace:
        details.append(f"Nhịp chuyến đi: {memory.pace}")
    if memory.interests:
        details.append(f"Ưu tiên trải nghiệm: {', '.join(memory.interests)}")
    if not details:
        return None
    return (
        "[CONVERSATION_MEMORY]\n"
        "Dùng các thông tin đã ghi nhận dưới đây; không hỏi lại trường đã có. "
        "Thông tin trong tin nhắn mới hơn được ưu tiên.\n"
        + "\n".join(details)
        + "\n[/CONVERSATION_MEMORY]"
    )
