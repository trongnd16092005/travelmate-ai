from functools import lru_cache

from app.clients.llm import create_chat_model
from app.clients.llm.base import ChatMessage, ChatModel
from app.core.config import settings
from app.knowledge.destinations import (
    DESTINATIONS,
    DestinationKnowledge,
    normalize_lookup_key,
    resolve_destination,
)
from app.prompts.chat import CHAT_SYSTEM_PROMPT
from app.schemas.chat import ChatRequest, ChatResponse, TripContext

OUT_OF_SCOPE_MARKER = "[OUT_OF_SCOPE]"

OUT_OF_SCOPE_TERMS = (
    "viet code",
    "java",
    "python",
    "sap xep mang",
    "co phieu",
    "chung khoan",
    "mua coin",
    "gia coin",
    "xo so",
    "giai phuong trinh",
    "tich phan",
    "soan hop dong",
    "don kien",
    "sua may in",
)
TRANSACTION_TERMS = (
    "tru tien",
    "dat luon phong",
    "xoa het lich trinh",
    "xoa lich trinh",
    "huy phong",
    "gui tien coc",
    "thanh toan thay",
    "ky thay",
)
MEDICAL_TERMS = (
    "uong thuoc gi",
    "ke thuoc",
    "dang sot",
    "sot cao",
    "dau nguc",
    "kho tho",
)
WEATHER_RISK_TERMS = (
    "mua lon",
    "canh bao bao",
    "canh bao song lon",
    "lu quet",
    "sat lo",
    "duong deo bi cam",
)
ALLERGY_TERMS = ("di ung", "soc phan ve")
VULNERABLE_TRAVELER_TERMS = (
    "hon 70 tuoi",
    "tren 70 tuoi",
    "nguoi cao tuoi",
    "em be",
    "tre so sinh",
)


class ChatService:
    def __init__(self, model: ChatModel, provider: str) -> None:
        self.model = model
        self.provider = provider

    def chat(self, request: ChatRequest) -> ChatResponse:
        guardrail = self._guardrail_reply(request.message)
        if guardrail is not None:
            reply, is_out_of_scope = guardrail
            return ChatResponse(
                reply=reply,
                isOutOfScope=is_out_of_scope,
                suggestedQuestions=self._suggest_questions(request.trip_context),
                provider=self.provider,
            )
        messages = self.build_messages(request)
        raw_reply = self.model.generate(messages).strip()
        fallback = self._validate_model_reply(request, raw_reply)
        if fallback is not None:
            raw_reply = fallback
        is_out_of_scope = raw_reply.startswith(OUT_OF_SCOPE_MARKER)
        reply = raw_reply.removeprefix(OUT_OF_SCOPE_MARKER).strip()
        return ChatResponse(
            reply=reply,
            is_out_of_scope=is_out_of_scope,
            suggested_questions=self._suggest_questions(request.trip_context),
            provider=self.provider,
        )

    @staticmethod
    def _guardrail_reply(message: str) -> tuple[str, bool] | None:
        normalized = normalize_lookup_key(message)
        if any(term in normalized for term in OUT_OF_SCOPE_TERMS):
            return (
                (
                    "Yêu cầu này không thuộc phạm vi trợ lý du lịch. Mình có thể hỗ trợ điểm đến, "
                    "lịch trình, ngân sách hoặc chuẩn bị thông tin cho chuyến đi."
                ),
                True,
            )
        if any(term in normalized for term in TRANSACTION_TERMS):
            return (
                (
                    "Mình không thể tự thực hiện giao dịch, thanh toán, xóa hoặc thay đổi dữ liệu "
                    "thay bạn. Mình có thể chuẩn bị phương án để bạn xem lại và tự xác nhận."
                ),
                False,
            )
        if any(term in normalized for term in MEDICAL_TERMS):
            return (
                (
                    "Ưu tiên an toàn: mình không thể chẩn đoán hoặc kê thuốc. Bạn nên liên hệ bác "
                    "sĩ hoặc cơ sở y tế trước khi tiếp tục chuyến đi; nếu có khó thở, đau ngực, "
                    "lơ mơ hoặc triệu chứng nặng, hãy tìm trợ giúp y tế khẩn cấp."
                ),
                False,
            )
        if any(term in normalized for term in WEATHER_RISK_TERMS):
            return (
                (
                    "Ưu tiên an toàn: không nên tiếp tục qua đèo, xuống biển hoặc đi vào vùng "
                    "đang có cảnh báo thời tiết nguy hiểm. Hãy kiểm tra thông báo chính thức, "
                    "hoãn hoặc đổi tuyến và làm theo hướng dẫn của cơ quan địa phương/cứu hộ."
                ),
                False,
            )
        if any(term in normalized for term in ALLERGY_TERMS):
            return (
                (
                    "Ưu tiên an toàn: mình không thể bảo đảm một món không có chất gây dị ứng. "
                    "Bạn nên tránh tác nhân đã biết, báo rõ dị ứng với nơi phục vụ, kiểm tra từng "
                    "thành phần và chuẩn bị phương án cấp cứu theo hướng dẫn của bác sĩ."
                ),
                False,
            )
        if any(term in normalized for term in VULNERABLE_TRAVELER_TERMS):
            return (
                (
                    "Mình sẽ ưu tiên lịch nhẹ, ít đi bộ và có thời gian nghỉ, nhưng cần thêm số "
                    "ngày, ngày đi và khả năng di chuyển cụ thể. Hãy kiểm tra khả năng tiếp cận "
                    "của từng địa điểm trước khi chốt lịch cho trẻ nhỏ hoặc người cao tuổi."
                ),
                False,
            )
        return None

    @classmethod
    def _validate_model_reply(cls, request: ChatRequest, reply: str) -> str | None:
        if not reply or normalize_lookup_key(reply) == normalize_lookup_key(request.message):
            return (
                "Mình chưa tạo được câu trả lời đủ tin cậy cho yêu cầu này. Bạn hãy bổ sung điểm "
                "đến, thời gian, số người và ngân sách; thông tin an toàn hoặc thời gian thực cần "
                "được kiểm tra từ nguồn hiện tại trước khi quyết định."
            )

        destination = cls._target_destination(request)
        if destination is None:
            return None
        normalized_reply = normalize_lookup_key(reply)
        for candidate in DESTINATIONS:
            if candidate.id == destination.id:
                continue
            for place in candidate.places:
                if cls._contains_phrase(normalized_reply, normalize_lookup_key(place.name)):
                    return (
                        f"Mình phát hiện gợi ý địa điểm chưa khớp với {destination.name}, nên sẽ "
                        "không đưa thẳng vào lịch. Hãy dùng chức năng tạo lịch trình có grounding "
                        "hoặc kiểm tra địa điểm bằng nguồn đáng tin cậy trước khi chốt."
                    )
        return None

    @classmethod
    def _target_destination(cls, request: ChatRequest) -> DestinationKnowledge | None:
        if request.trip_context:
            destination = resolve_destination(request.trip_context.destination)
            if destination is not None:
                return destination

        normalized_message = normalize_lookup_key(request.message)
        matches: list[tuple[int, DestinationKnowledge]] = []
        for destination in DESTINATIONS:
            for value in (destination.name, *destination.aliases):
                key = normalize_lookup_key(value)
                index = normalized_message.rfind(key)
                if index >= 0 and cls._contains_phrase(normalized_message, key):
                    matches.append((index, destination))
        return max(matches, key=lambda match: match[0])[1] if matches else None

    @staticmethod
    def _contains_phrase(normalized_text: str, normalized_phrase: str) -> bool:
        return f" {normalized_phrase} " in f" {normalized_text} "

    def build_messages(self, request: ChatRequest) -> list[ChatMessage]:
        messages: list[ChatMessage] = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        if request.trip_context:
            messages.append(
                {
                    "role": "system",
                    "content": self._format_trip_context(request.trip_context),
                }
            )
        messages.extend(message.model_dump() for message in request.history[-10:])
        messages.append({"role": "user", "content": request.message})
        return messages

    @staticmethod
    def _format_trip_context(context: TripContext) -> str:
        details = [f"Điểm đến: {context.destination}"]
        if context.start_date:
            details.append(f"Ngày bắt đầu: {context.start_date.isoformat()}")
        if context.end_date:
            details.append(f"Ngày kết thúc: {context.end_date.isoformat()}")
        if context.budget_vnd is not None:
            details.append(f"Ngân sách: {context.budget_vnd:,} VND")
        if context.num_people is not None:
            details.append(f"Số người: {context.num_people}")
        return "[TRIP_CONTEXT]\n" + "\n".join(details) + "\n[/TRIP_CONTEXT]"

    @staticmethod
    def _suggest_questions(context: TripContext | None) -> list[str]:
        if context:
            return [
                f"Nên đi đâu ở {context.destination}?",
                "Ngân sách nên chia như thế nào?",
                "Cần chuẩn bị những gì cho chuyến đi?",
            ]
        return [
            "Bạn muốn đi đâu?",
            "Bạn dự định đi trong bao nhiêu ngày?",
            "Ngân sách dự kiến là bao nhiêu?",
        ]


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(create_chat_model(settings), settings.llm_provider)
