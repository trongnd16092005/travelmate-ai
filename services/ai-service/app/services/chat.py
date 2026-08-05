import re
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
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.conversation import (
    ConversationMemory,
    build_conversation_memory,
    format_conversation_memory,
)

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
        memory = build_conversation_memory(request)
        guardrail = self._guardrail_reply(request.message)
        if guardrail is not None:
            reply, is_out_of_scope = guardrail
            return ChatResponse(
                reply=reply,
                isOutOfScope=is_out_of_scope,
                suggestedQuestions=self._suggest_questions(memory),
                provider=self.provider,
            )
        messages = self.build_messages(request)
        raw_reply = self.model.generate(messages).strip()
        fallback = self._validate_model_reply(request, raw_reply, memory)
        if fallback is not None:
            raw_reply = fallback
        is_out_of_scope = raw_reply.startswith(OUT_OF_SCOPE_MARKER)
        reply = self._to_plain_text(raw_reply.removeprefix(OUT_OF_SCOPE_MARKER))
        return ChatResponse(
            reply=reply,
            is_out_of_scope=is_out_of_scope,
            suggested_questions=self._suggest_questions(memory),
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
    def _validate_model_reply(
        cls,
        request: ChatRequest,
        reply: str,
        memory: ConversationMemory,
    ) -> str | None:
        if not reply or normalize_lookup_key(reply) == normalize_lookup_key(request.message):
            return (
                "Mình chưa tạo được câu trả lời đủ tin cậy cho yêu cầu này. Bạn hãy bổ sung điểm "
                "đến, thời gian, số người và ngân sách; thông tin an toàn hoặc thời gian thực cần "
                "được kiểm tra từ nguồn hiện tại trước khi quyết định."
            )

        previous_assistant = next(
            (
                message.content
                for message in reversed(request.history)
                if message.role == "assistant"
            ),
            None,
        )
        if previous_assistant and normalize_lookup_key(reply) == normalize_lookup_key(
            previous_assistant
        ):
            return cls._progress_reply(memory)
        if cls._asks_for_known_information(reply, memory):
            return cls._progress_reply(memory)

        destination = cls._target_destination(memory)
        if destination is None:
            return None
        normalized_reply = normalize_lookup_key(reply)
        for candidate in DESTINATIONS:
            if candidate.id == destination.id:
                continue
            if cls._mentions_destination(normalized_reply, candidate):
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
    def _mentions_destination(
        cls,
        normalized_text: str,
        destination: DestinationKnowledge,
    ) -> bool:
        return any(
            cls._contains_phrase(normalized_text, normalize_lookup_key(value))
            for value in (destination.name, *destination.aliases)
        )

    @staticmethod
    def _target_destination(memory: ConversationMemory) -> DestinationKnowledge | None:
        return resolve_destination(memory.destination) if memory.destination else None

    @staticmethod
    def _progress_reply(memory: ConversationMemory) -> str:
        if not memory.destination:
            if memory.region == "Miền Trung":
                group = f" cho nhóm {memory.num_people} người" if memory.num_people else ""
                return (
                    f"Ở Miền Trung{group}, bạn có thể cân nhắc Huế nếu thích văn hóa, "
                    "Đà Nẵng–Hội An nếu muốn kết hợp biển và phố cổ, hoặc Quảng Bình "
                    "nếu thích thiên nhiên. Bạn thích trải nghiệm theo hướng nào nhất?"
                )
            return "Bạn muốn mình gợi ý điểm đến theo khu vực hoặc loại trải nghiệm nào?"
        if not memory.duration_days:
            return f"Mình đã ghi nhận điểm đến {memory.destination}. Bạn dự định đi bao nhiêu ngày?"
        if not memory.num_people:
            return "Mình đã ghi nhận thời lượng chuyến đi. Chuyến này có bao nhiêu người?"
        if memory.budget_vnd is None:
            return "Mình đã ghi nhận số người và thời lượng. Tổng ngân sách dự kiến là bao nhiêu?"
        return (
            f"Mình đã ghi nhận chuyến {memory.destination} {memory.duration_days} ngày cho "
            f"{memory.num_people} người với ngân sách {memory.budget_vnd:,} VND. "
            "Ngân sách này đã gồm chi phí di chuyển đến điểm đến chưa?"
        )

    @staticmethod
    def _asks_for_known_information(reply: str, memory: ConversationMemory) -> bool:
        normalized = normalize_lookup_key(reply)
        missing_claim = any(
            term in normalized for term in ("chua co", "con thieu", "thieu thong tin")
        )
        if missing_claim:
            known_labels = (
                (memory.destination, ("diem den",)),
                (memory.duration_days, ("so ngay", "thoi luong")),
                (memory.num_people, ("so nguoi", "so khach")),
                (memory.budget_vnd, ("ngan sach",)),
            )
            if any(
                value is not None and any(label in normalized for label in labels)
                for value, labels in known_labels
            ):
                return True

        known_questions = (
            (memory.destination, ("muon di dau", "diem den nao")),
            (memory.duration_days, ("bao nhieu ngay", "may ngay")),
            (memory.num_people, ("bao nhieu nguoi", "may nguoi", "bao nhieu khach")),
            (memory.budget_vnd, ("ngan sach bao nhieu", "bao nhieu ngan sach")),
        )
        return any(
            value is not None and any(question in normalized for question in questions)
            for value, questions in known_questions
        )

    @staticmethod
    def _contains_phrase(normalized_text: str, normalized_phrase: str) -> bool:
        return f" {normalized_phrase} " in f" {normalized_text} "

    @staticmethod
    def _to_plain_text(reply: str) -> str:
        lines: list[str] = []
        blank = False
        for raw_line in reply.strip().splitlines():
            line = re.sub(r"^\s*#{1,6}\s*", "", raw_line)
            line = re.sub(r"^\s*[-*]\s+", "• ", line)
            line = line.replace("**", "").replace("__", "").replace("`", "")
            line = line.strip()
            if not line:
                if lines and not blank:
                    lines.append("")
                blank = True
                continue
            lines.append(line)
            blank = False
        return "\n".join(lines).strip()

    def build_messages(self, request: ChatRequest) -> list[ChatMessage]:
        messages: list[ChatMessage] = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        memory_text = format_conversation_memory(build_conversation_memory(request))
        if memory_text:
            messages.append(
                {
                    "role": "system",
                    "content": memory_text,
                }
            )
        messages.extend(message.model_dump() for message in request.history[-10:])
        messages.append({"role": "user", "content": request.message})
        return messages

    @staticmethod
    def _suggest_questions(memory: ConversationMemory) -> list[str]:
        if memory.destination:
            return [
                f"Nên đi đâu ở {memory.destination}?",
                "Ngân sách nên chia như thế nào?",
                "Cần chuẩn bị những gì cho chuyến đi?",
            ]
        if memory.region:
            return [
                f"Gợi ý điểm đến ở {memory.region}",
                "Nơi nào phù hợp đi theo nhóm?",
                "Nên đi biển hay tham quan văn hóa?",
            ]
        return [
            "Bạn muốn đi đâu?",
            "Bạn dự định đi trong bao nhiêu ngày?",
            "Ngân sách dự kiến là bao nhiêu?",
        ]


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(create_chat_model(settings), settings.llm_provider)
