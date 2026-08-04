from functools import lru_cache

from app.clients.llm import create_chat_model
from app.clients.llm.base import ChatMessage, ChatModel
from app.core.config import settings
from app.knowledge.destinations import normalize_lookup_key
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
        return None

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
