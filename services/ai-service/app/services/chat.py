import re
from functools import lru_cache

from app.clients.llm import create_chat_model
from app.clients.llm.base import ChatMessage, ChatModel
from app.core.config import settings
from app.knowledge.destinations import (
    DESTINATIONS,
    RUNTIME_NATIONWIDE_DESTINATIONS,
    DestinationKnowledge,
    format_grounded_catalog_context,
    grounded_place_by_id,
    normalize_lookup_key,
    recommend_destinations,
    resolve_destination,
)
from app.prompts.chat import CHAT_SYSTEM_PROMPT
from app.retrieval.weather import (
    OpenMeteoWeatherProvider,
    WeatherProvider,
    describe_weather_code,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.conversation import (
    ConversationMemory,
    build_conversation_memory,
    format_conversation_memory,
    update_memory,
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
    def __init__(
        self,
        model: ChatModel,
        provider: str,
        model_version: str | None = None,
        weather_provider: WeatherProvider | None = None,
    ) -> None:
        self.model = model
        self.provider = provider
        self.model_version = model_version
        self.weather_provider = weather_provider

    def chat(self, request: ChatRequest) -> ChatResponse:
        if self._is_reset_request(request.message):
            return ChatResponse(
                reply=(
                    "Mình đã xóa ngữ cảnh chuyến cũ. Bạn muốn bắt đầu chuyến mới ở đâu?"
                ),
                is_out_of_scope=False,
                suggested_questions=[
                    "Gợi ý điểm đến miền Bắc",
                    "Gợi ý điểm đến miền Trung",
                    "Gợi ý điểm đến miền Nam",
                ],
                provider=self.provider,
                model_version=self.model_version,
                reset_context=True,
            )
        memory = build_conversation_memory(request)
        guardrail = self._guardrail_reply(request.message)
        if guardrail is not None:
            reply, is_out_of_scope = guardrail
            return ChatResponse(
                reply=reply,
                isOutOfScope=is_out_of_scope,
                suggestedQuestions=self._suggest_questions(memory),
                provider=self.provider,
                modelVersion=self.model_version,
            )
        clarification_reply = self._input_clarification_reply(request.message)
        if clarification_reply is not None:
            return ChatResponse(
                reply=clarification_reply,
                is_out_of_scope=False,
                suggested_questions=self._suggest_questions(memory),
                provider=self.provider,
                model_version=self.model_version,
            )
        realtime_reply = self._realtime_reply(request.message, memory)
        if realtime_reply is not None:
            return ChatResponse(
                reply=realtime_reply,
                is_out_of_scope=False,
                suggested_questions=self._suggest_questions(memory),
                provider=self.provider,
                model_version=self.model_version,
            )
        guided_reply = self._guided_reply(request, memory)
        if guided_reply is not None:
            return ChatResponse(
                reply=guided_reply,
                is_out_of_scope=False,
                suggested_questions=self._suggest_questions(memory),
                provider=self.provider,
                model_version=self.model_version,
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
            model_version=self.model_version,
        )

    def _realtime_reply(
        self,
        message: str,
        memory: ConversationMemory,
    ) -> str | None:
        normalized = normalize_lookup_key(message)
        operating_info_intent = any(
            term in normalized
            for term in (
                "gio hoat dong",
                "gio mo cua",
                "mo cua luc",
                "may gio mo cua",
                "gia ve",
                "ve bao nhieu",
                "phi tham quan",
            )
        )
        if operating_info_intent:
            destination = self._target_destination(memory)
            target = destination.name if destination else "địa điểm này"
            return (
                f"Mình chưa có nguồn realtime đã xác minh cho giá vé hoặc giờ hoạt động tại "
                f"{target}, nên không tự đưa ra con số hay khung giờ. Bạn hãy kiểm tra website, "
                "fanpage hoặc thông báo chính thức của từng địa điểm trước khi đi."
            )
        weather_intent = any(
            term in normalized
            for term in ("thoi tiet", "du bao", "nhiet do", "mua khong", "co mua")
        )
        if not weather_intent:
            return None
        destination = self._target_destination(memory)
        if destination is None:
            return "Bạn muốn kiểm tra thời tiết cho tỉnh/thành hoặc điểm đến nào?"
        if self.weather_provider is None:
            return (
                f"Mình chưa kết nối được nguồn thời tiết hiện tại cho {destination.name}, nên "
                "không khẳng định trời mưa hay nắng. Hãy kiểm tra dự báo chính thức trước khi "
                "chốt lịch hoặc thực hiện hoạt động ngoài trời."
            )
        snapshot = self.weather_provider.get_current(destination.name)
        if snapshot is None:
            return (
                f"Nguồn realtime hiện không trả được dữ liệu cho {destination.name}. Mình sẽ "
                "không dùng dữ liệu cũ hoặc tự đoán; bạn hãy thử lại sau và kiểm tra cảnh báo "
                "chính thức trước khi đi."
            )
        probability = ""
        if snapshot.daily_precipitation_probability_max is not None:
            probability = (
                " Xác suất mưa cao nhất trong ngày theo mô hình là "
                f"{snapshot.daily_precipitation_probability_max}%."
            )
        return (
            f"Dự báo hiện tại cho {destination.name} lúc {snapshot.observed_at}: "
            f"{describe_weather_code(snapshot.weather_code)}, "
            f"{snapshot.temperature_c:g}°C (cảm giác {snapshot.apparent_temperature_c:g}°C), "
            f"lượng mưa {snapshot.precipitation_mm:g} mm và gió "
            f"{snapshot.wind_speed_kmh:g} km/h.{probability} "
            "Thông tin có thể thay đổi; hãy ưu tiên cảnh báo chính thức tại địa phương."
        )

    @staticmethod
    def _input_clarification_reply(message: str) -> str | None:
        normalized = normalize_lookup_key(message)
        compact_tokens = normalized.split()
        has_mixed_token = any(
            re.search(r"[a-z]\d|\d[a-z]", token) for token in compact_tokens
        )
        if has_mixed_token and len(normalized) <= 30:
            return (
                f"Mình chưa hiểu rõ “{message.strip()}”. Nếu bạn đang nhập số người hoặc số "
                "ngày, hãy viết rõ như “2 người” hoặc “3 ngày”; nếu không, bạn hãy diễn đạt "
                "lại yêu cầu bằng một câu ngắn."
            )
        return None

    @staticmethod
    def _is_reset_request(message: str) -> bool:
        normalized = normalize_lookup_key(message)
        exact_requests = {
            "dat lai",
            "reset",
            "bat dau lai",
            "bat dau chuyen moi",
            "tao chuyen moi",
            "xoa thong tin chuyen cu",
            "xoa du lieu chuyen cu",
            "lam lai tu dau",
            "chuyen khac",
            "doi chuyen",
            "di noi khac",
            "toi muon mot chuyen khac",
            "toi muon di noi khac",
        }
        return normalized in exact_requests or any(
            phrase in normalized
            for phrase in (
                "reset du lieu chuyen di",
                "dat lai thong tin chuyen di",
                "xoa ngu canh chuyen cu",
                "bo het thong tin chuyen cu",
                "bat dau ke hoach moi",
                "bat dau mot chuyen khac",
                "doi sang chuyen moi",
                "lam lai tu dau",
                "chuyen khac",
                "doi chuyen",
                "di noi khac",
            )
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
        allowed_places = tuple(grounded_place_by_id(destination).values())
        suggests_a_place = any(
            marker in normalized_reply
            for marker in (
                "hay ghe",
                "co the ghe",
                "nen ghe",
                "tham quan",
                "check in",
                "diem den",
            )
        )
        mentions_allowed_place = any(
            cls._contains_phrase(normalized_reply, normalize_lookup_key(place.name))
            for place in allowed_places
        )
        if suggests_a_place and not mentions_allowed_place:
            return cls._grounded_recommendation_reply(memory, include_food=False)
        for candidate in (*RUNTIME_NATIONWIDE_DESTINATIONS, *DESTINATIONS):
            canonical_candidate = resolve_destination(candidate.name) or candidate
            if canonical_candidate.name == destination.name:
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
            if memory.region and memory.interests:
                recommendations = recommend_destinations(
                    region=memory.region,
                    themes=memory.interests,
                    limit=5,
                )
                if recommendations:
                    preference = ", ".join(memory.interests)
                    options = "; ".join(
                        f"{destination.name} ({', '.join(place.name for place in destination.places[:2])})"
                        for destination in recommendations
                    )
                    return (
                        f"Với ưu tiên {preference} ở {memory.region}, mình gợi ý: {options}. "
                        "Bạn chọn một nơi, mình sẽ lên lịch và phân bổ ngân sách theo số ngày."
                    )
            if memory.region == "Miền Trung":
                group = f" cho nhóm {memory.num_people} người" if memory.num_people else ""
                return (
                    f"Ở Miền Trung{group}, bạn có thể cân nhắc Huế nếu thích văn hóa, "
                    "Đà Nẵng–Hội An nếu muốn kết hợp biển và phố cổ, hoặc Quảng Bình "
                    "nếu thích thiên nhiên. Bạn thích trải nghiệm theo hướng nào nhất?"
                )
            if memory.region == "Miền Bắc":
                return (
                    "Ở Miền Bắc, bạn có thể cân nhắc Hà Nội nếu thích văn hóa đô thị, "
                    "Ninh Bình nếu thích cảnh quan thiên nhiên, hoặc Sa Pa nếu muốn trải "
                    "nghiệm vùng núi. Bạn thích hướng nào nhất?"
                )
            if memory.region == "Miền Nam":
                return (
                    "Ở Miền Nam, bạn có thể cân nhắc TP. Hồ Chí Minh cho trải nghiệm đô thị, "
                    "Phú Quốc nếu thích biển, hoặc Cần Thơ nếu muốn khám phá miền sông nước. "
                    "Bạn thích hướng nào nhất?"
                )
            if memory.region == "Tây Nguyên":
                return (
                    "Ở Tây Nguyên, bạn có thể cân nhắc Đà Lạt nếu thích khí hậu mát mẻ hoặc "
                    "Buôn Ma Thuột nếu quan tâm văn hóa và cà phê. Bạn thích hướng nào nhất?"
                )
            return "Bạn muốn mình gợi ý điểm đến theo khu vực hoặc loại trải nghiệm nào?"
        if not memory.duration_days:
            return f"Mình đã ghi nhận điểm đến {memory.destination}. Bạn dự định đi bao nhiêu ngày?"
        if not memory.num_people:
            return "Mình đã ghi nhận thời lượng chuyến đi. Chuyến này có bao nhiêu người?"
        if memory.budget_vnd is None:
            return (
                f"Mình đã ghi nhận chuyến {memory.destination} {memory.duration_days} ngày cho "
                f"{memory.num_people} người. Tổng ngân sách dự kiến là bao nhiêu?"
            )
        budget = f"{memory.budget_vnd:,}".replace(",", ".")
        if memory.transport_included is not None:
            transport = "đã bao gồm" if memory.transport_included else "chưa bao gồm"
            return (
                f"Mình đã ghi nhận chuyến {memory.destination} {memory.duration_days} ngày cho "
                f"{memory.num_people} người với ngân sách {budget} VND, {transport} chi phí "
                "di chuyển đến điểm đến. Bạn muốn mình hỗ trợ lập lịch trình, phân bổ ngân sách "
                "hay chuẩn bị checklist?"
            )
        return (
            f"Mình đã ghi nhận chuyến {memory.destination} {memory.duration_days} ngày cho "
            f"{memory.num_people} người với ngân sách {budget} VND. "
            "Ngân sách này đã gồm chi phí di chuyển đến điểm đến chưa?"
        )

    @classmethod
    def _guided_reply(
        cls,
        request: ChatRequest,
        memory: ConversationMemory,
    ) -> str | None:
        normalized = normalize_lookup_key(request.message)
        supplied = update_memory(ConversationMemory(), request.message)
        destination_selection = (
            supplied.destination is not None
            and len(normalized.split()) <= 8
            and not any(
                marker in normalized
                for marker in ("thay cho", "thay vi", " bang ", " sang ", " qua ", "doi ", "chuyen ")
            )
            and (
                normalized.startswith(("di ", "chon ", "chot ", "toi chon "))
                or normalized == normalize_lookup_key(supplied.destination)
            )
        )
        if destination_selection:
            destination = cls._target_destination(memory)
            choice = re.sub(
                r"^(?:tôi\s+)?(?:đi|chọn|chốt)\s+",
                "",
                request.message.strip(),
                flags=re.IGNORECASE,
            ).strip()
            if (
                destination is not None
                and choice
                and normalize_lookup_key(choice) != normalize_lookup_key(destination.name)
                and memory.duration_days is None
            ):
                return (
                    f"Mình đã ghi nhận {choice} thuộc {destination.name}. "
                    "Bạn dự định đi bao nhiêu ngày?"
                )
            return cls._progress_reply(memory)
        reasoning_reply = cls._reasoning_reply(normalized, memory)
        if reasoning_reply is not None:
            return reasoning_reply
        previous_assistant = next(
            (
                normalize_lookup_key(message.content)
                for message in reversed(request.history)
                if message.role == "assistant"
            ),
            "",
        )
        preparation_intent = any(
            term in normalized
            for term in ("can chuan bi", "chuan bi gi", "mang gi", "checklist", "can gi cho chuyen")
        )
        itinerary_intent = any(
            term in normalized
            for term in ("lap lich", "len lich", "xep lich", "lich trinh", "lich di")
        ) or (
            "theo diem den" in normalized
            and any(
                term in previous_assistant
                for term in ("lap lich", "lich trinh", "goi y diem den cu the")
            )
        )
        budget_intent = any(
            term in normalized
            for term in (
                "phan bo ngan sach",
                "chia ngan sach",
                "ngan sach nen chia",
                "du toan chi phi",
            )
        ) or (
            "theo ngay" in normalized
            and any(term in previous_assistant for term in ("phan bo ngan sach", "chia ngan sach"))
        )
        intent_replies: list[str] = []
        if itinerary_intent:
            intent_replies.append(cls._itinerary_reply(memory))
        if budget_intent:
            intent_replies.append(cls._budget_reply(memory))
        if preparation_intent:
            intent_replies.append(cls._preparation_reply(memory))
        if intent_replies:
            return "\n\n".join(intent_replies)
        recommendation_intent = "goi y" in normalized or "nen di dau" in normalized
        grounded_place_intent = recommendation_intent or any(
            term in normalized
            for term in (
                "diem tham quan",
                "tham quan gi",
                "cho nao",
                "ba diem",
                "3 diem",
                "an gi",
                "mon ngon",
                "dac san",
                "am thuc",
            )
        )
        if grounded_place_intent and memory.destination:
            requested_place_limit = (
                3
                if any(term in normalized for term in ("ba diem", "3 diem"))
                else None
            )
            return cls._grounded_recommendation_reply(
                memory,
                include_food=any(
                    term in normalized
                    for term in ("an gi", "mon ngon", "dac san", "am thuc")
                ),
                limit=requested_place_limit,
            )
        planning_intent = any(
            term in normalized
            for term in (
                "chuyen di",
                "can chuyen",
                "du lich",
                "muon di",
                "di choi",
                "can di",
                "di tai",
            )
        )
        if planning_intent and not memory.destination and not memory.region:
            if memory.duration_days:
                return (
                    f"Mình đã ghi nhận chuyến {memory.duration_days} ngày. Bạn muốn đi điểm đến "
                    "hoặc khu vực nào?"
                )
            return (
                "Bạn muốn đi điểm đến hoặc khu vực nào, trong khoảng bao nhiêu ngày? "
                "Nếu đã có ngân sách dự kiến, bạn có thể cho mình biết luôn."
            )
        if memory.region and not memory.destination:
            if recommendation_intent:
                return cls._progress_reply(memory)
            if planning_intent:
                group = f" cho {memory.num_people} người" if memory.num_people else ""
                return (
                    f"Mình đã ghi nhận chuyến {memory.region}{group}. Bạn muốn ưu tiên biển, "
                    "văn hóa hay thiên nhiên để mình gợi ý điểm đến phù hợp?"
                )

        supplied_slot = any(
            value is not None
            for value in (
                supplied.destination,
                supplied.duration_days,
                supplied.num_people,
                supplied.budget_vnd,
                supplied.region,
                supplied.pace,
            )
        ) or bool(supplied.interests)
        explicit_intent = any(
            term in normalized
            for term in (
                "goi y",
                "lich trinh",
                "lap lich",
                "nen ",
                "di dau",
                "an gi",
                "chuan bi",
                "mang gi",
                "checklist",
            )
        )
        if memory.last_answered_slot == "transport_included":
            return cls._progress_reply(memory)
        correction_intent = any(
            term in normalized for term in ("doi ", "cap nhat", "sua ", "thanh ")
        )
        if correction_intent and supplied_slot and not (
            itinerary_intent or budget_intent or preparation_intent
        ):
            return cls._progress_reply(memory)
        if supplied.region and memory.destination and len(normalized.split()) <= 5:
            return (
                f"{memory.destination} thuộc {supplied.region}. Mình vẫn giữ {memory.destination} "
                "là điểm đến hiện tại; nếu bạn muốn mở rộng sang nơi khác trong vùng, hãy nói rõ "
                "để mình điều chỉnh."
            )
        if supplied_slot and len(normalized.split()) <= 24 and not explicit_intent:
            return cls._progress_reply(memory)
        return None

    @classmethod
    def _grounded_recommendation_reply(
        cls,
        memory: ConversationMemory,
        *,
        include_food: bool,
        limit: int | None = None,
    ) -> str:
        destination = cls._target_destination(memory)
        if destination is None:
            return (
                f"TravelMate chưa có catalog được kiểm chứng cho {memory.destination}. "
                "Mình sẽ không tự tạo tên địa điểm; bạn hãy chọn một tỉnh/thành đang được hỗ trợ."
            )
        selected_places = destination.places[:limit] if limit is not None else destination.places
        places = ", ".join(place.name for place in selected_places)
        count_label = "ba" if len(selected_places) == 3 else str(len(selected_places))
        parts = [
            (
                f"Mình đã đối chiếu catalog TravelMate cho {destination.name}: "
                f"{count_label} điểm có thể cân nhắc là {places}."
            )
        ]
        if include_food:
            foods = ", ".join(destination.foods[:3])
            parts.append(f"Các món trong catalog gồm {foods}.")
        return " ".join(parts)

    @classmethod
    def _reasoning_reply(
        cls,
        normalized: str,
        memory: ConversationMemory,
    ) -> str | None:
        destination = cls._target_destination(memory)
        realtime_terms = (
            "mo cua",
            "hoat dong binh thuong",
            "khong mua",
            "thoi tiet",
            "du bao",
        )
        uncertainty_intent = any(term in normalized for term in realtime_terms) and any(
            term in normalized for term in ("chac", "dung khong", "co chac")
        )
        if uncertainty_intent:
            target = destination.name if destination else "điểm đến này"
            fallback = (
                destination.places[0].name
                if destination and destination.places
                else "một hoạt động trong nhà hoặc dễ đổi lịch"
            )
            return (
                f"Mình chưa thể khẳng định thời tiết hoặc tình trạng hoạt động tại {target} "
                "khi chưa có nguồn hiện tại. Hãy kiểm tra dự báo chính thức và thông báo của "
                "địa điểm trước khi chốt; nếu điều kiện phù hợp thì giữ kế hoạch, nếu không thì "
                f"chuyển sang {fallback}."
            )

        sequence_intent = any(
            term in normalized
            for term in ("den muon", "toi ngay 1", "toi ngay dau", "toi moi den")
        ) and any(
            term in normalized
            for term in ("ve som", "roi di som", "sang ngay 3", "ngay cuoi ve")
        )
        if sequence_intent and destination:
            first = destination.places[0].name
            second = destination.places[1].name
            third = destination.places[2].name
            return (
                "Ngày 1 đến muộn: chỉ nhận phòng, ăn gần nơi ở và nghỉ. "
                f"Ngày 2 là ngày tham quan chính: ưu tiên {first}, sau đó thêm {second} nếu "
                "thời gian thực tế cho phép. Ngày 3 rời đi sớm nên không xếp "
                f"{third}; cách này tránh nhồi hoạt động vào hai ngày di chuyển."
            )

        aspirational_terms = (
            "cao cap",
            "an ngon",
            "dac san moi bua",
            "tham quan het",
            "di du ba diem",
            "moi diem noi bat",
        )
        infeasible_intent = (
            memory.budget_vnd is not None
            and memory.num_people is not None
            and memory.duration_days is not None
            and sum(term in normalized for term in aspirational_terms) >= 2
        )
        if infeasible_intent:
            daily = memory.budget_vnd // memory.num_people // memory.duration_days
            daily_text = f"{daily:,}".replace(",", ".")
            total_text = f"{memory.budget_vnd:,}".replace(",", ".")
            place_priority = (
                ""
                if destination is None
                else (
                    f", chỉ ưu tiên {destination.places[0].name} và "
                    f"{destination.places[1].name}"
                )
            )
            return (
                f"Ngân sách {total_text} VND cho {memory.num_people} người trong "
                f"{memory.duration_days} ngày tương đương khoảng {daily_text} VND/người/ngày "
                "cho toàn bộ chuyến, nên yêu cầu cao cấp, ăn ngon và tham quan hết khó khả thi "
                "đồng thời. Bạn có thể giữ ngân sách nhưng giảm số ngày, chọn lưu trú tiết kiệm"
                f"{place_priority}; hoặc giữ thời lượng và tăng ngân sách/hạ tiêu chuẩn lưu trú. "
                "Mình không tự gán giá phòng khi chưa kiểm tra nguồn hiện tại."
            )

        vulnerable_terms = ("tre nho", "nguoi lon tuoi", "nguoi cao tuoi", "em be")
        pacing_terms = ("khong qua met", "lich nhe", "thu tha", "chua thoi gian nghi")
        constraint_intent = any(term in normalized for term in vulnerable_terms) and any(
            term in normalized for term in pacing_terms
        )
        if constraint_intent and destination:
            duration = memory.duration_days or 3
            return (
                "Mình ưu tiên sức khỏe trước số lượng điểm: mỗi ngày một điểm chính, xen kẽ "
                f"ngày nhẹ và ngày tham quan trong {duration} ngày ở {destination.name}. Chọn "
                f"{destination.places[0].name} và {destination.places[1].name} làm hai điểm "
                f"chính; {destination.places[2].name} chỉ thêm nếu trẻ nhỏ và người lớn tuổi "
                "vẫn thoải mái. Cách này giữ được thời gian nghỉ mà không làm chuyến đi quá đơn điệu."
            )

        comparison_intent = any(
            term in normalized for term in ("so sanh", "phan van", "giua ", "chon phuong an")
        )
        mentioned = [
            candidate
            for candidate in DESTINATIONS
            if cls._mentions_destination(normalized, candidate)
        ]
        if comparison_intent and len(mentioned) >= 2:
            requested_theme = next(
                (
                    theme
                    for candidate in mentioned
                    for theme in candidate.themes
                    if normalize_lookup_key(theme) in normalized
                ),
                None,
            )
            chosen = next(
                (
                    candidate
                    for candidate in mentioned
                    if requested_theme and requested_theme in candidate.themes
                ),
                mentioned[0],
            )
            alternative = next(candidate for candidate in mentioned if candidate.id != chosen.id)
            criterion = requested_theme or chosen.themes[0]
            return (
                f"Theo tiêu chí {criterion}, mình chọn {chosen.name} vì danh mục đã xác thực có "
                f"{chosen.places[0].name} và {chosen.places[1].name}, phù hợp hơn với ưu tiên này. "
                f"{alternative.name} vẫn đáng cân nhắc nếu bạn chuyển trọng tâm sang "
                f"{alternative.themes[0]}."
            )
        return None

    @staticmethod
    def _preparation_reply(memory: ConversationMemory) -> str:
        destination = memory.destination or "điểm đến"
        duration = f" trong {memory.duration_days} ngày" if memory.duration_days else ""
        return (
            f"Checklist cho {destination}{duration}; trước hết hãy chuẩn bị giấy tờ tùy thân:\n"
            "• Giấy tờ: CCCD/hộ chiếu, vé và xác nhận nơi ở.\n"
            "• Tài chính: tiền mặt dự phòng, thẻ và hạn mức chi tiêu.\n"
            "• Cá nhân: thuốc đang dùng, đồ vệ sinh, sạc và pin dự phòng.\n"
            "• Trang phục: quần áo theo thời tiết, giày dễ đi và đồ chống nắng/mưa.\n"
            "• Trước khi đi: kiểm tra thời tiết, giờ hoạt động, phương tiện và cảnh báo địa phương."
        )

    @classmethod
    def _itinerary_reply(cls, memory: ConversationMemory) -> str:
        if not memory.destination:
            return "Để lập lịch ngay, bạn muốn chọn điểm đến cụ thể nào?"
        if not memory.duration_days:
            return f"Để lập lịch {memory.destination}, bạn dự định đi bao nhiêu ngày?"
        destination = cls._target_destination(memory)
        if destination is None:
            return (
                f"TravelMate chưa có danh mục địa điểm được xác thực cho {memory.destination}. "
                "Bạn có thể chọn một điểm đến trong catalog để mình lập lịch grounded."
            )
        group = f" cho {memory.num_people} người" if memory.num_people else ""
        lines = [f"Lịch gợi ý {memory.duration_days} ngày tại {destination.name}{group}:"]
        for day in range(1, memory.duration_days + 1):
            place = destination.places[(day - 1) % len(destination.places)]
            food = destination.foods[(day - 1) % len(destination.foods)]
            lines.append(
                f"Ngày {day}: sáng tham quan {place.name}; trưa thử {food}; "
                "chiều nghỉ hoặc khám phá khu vực lân cận; tối tự do."
            )
        lines.append(
            "Hãy kiểm tra thời tiết, giờ hoạt động và thời gian di chuyển thực tế trước khi chốt."
        )
        return "\n".join(lines)

    @staticmethod
    def _budget_reply(memory: ConversationMemory) -> str:
        if memory.budget_vnd is None:
            return "Để phân bổ ngân sách, tổng mức chi cho cả chuyến là bao nhiêu?"
        total = memory.budget_vnd
        accommodation = total * 35 // 100
        food = total * 25 // 100
        transport = total * 20 // 100
        activities = total * 15 // 100
        reserve = total - accommodation - food - transport - activities

        def format_vnd(value: int) -> str:
            return f"{value:,}".replace(",", ".") + " VND"

        destination = f" cho chuyến {memory.destination}" if memory.destination else ""
        group = f" của {memory.num_people} người" if memory.num_people else ""
        transport_scope = (
            "di chuyển toàn chuyến"
            if memory.transport_included
            else "di chuyển tại điểm đến"
        )
        return (
            f"Phân bổ tham khảo {format_vnd(total)}{destination}{group}:\n"
            f"• Lưu trú 35%: {format_vnd(accommodation)}.\n"
            f"• Ăn uống 25%: {format_vnd(food)}.\n"
            f"• {transport_scope.capitalize()} 20%: {format_vnd(transport)}.\n"
            f"• Tham quan 15%: {format_vnd(activities)}.\n"
            f"• Dự phòng 5%: {format_vnd(reserve)}.\n"
            "Đây là khung dự toán; giá thực tế cần được kiểm tra trước khi đặt dịch vụ."
        )

    @staticmethod
    def _asks_for_known_information(reply: str, memory: ConversationMemory) -> bool:
        normalized = normalize_lookup_key(reply)
        question_topics = (
            ("khoi hanh", "ngay di"),
            ("ngan sach", "chi phi"),
            ("bao nhieu ngay", "may ngay", "thoi luong"),
            ("bao nhieu nguoi", "may nguoi", "bao nhieu khach"),
            ("muon di dau", "diem den nao"),
        )
        if sum(any(term in normalized for term in topic) for topic in question_topics) > 1:
            return True

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
        memory = build_conversation_memory(request)
        memory_text = format_conversation_memory(memory)
        if memory_text:
            messages.append(
                {
                    "role": "system",
                    "content": memory_text,
                }
            )
        destination = self._target_destination(memory)
        if destination is not None:
            messages.append(
                {
                    "role": "system",
                    "content": format_grounded_catalog_context(destination),
                }
            )
        messages.extend(message.model_dump() for message in request.history[-8:])
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
    if settings.llm_provider == "local":
        model_version = settings.local_model_version
    elif settings.llm_provider == "groq":
        model_version = settings.groq_model
    else:
        model_version = None
    weather_provider = (
        OpenMeteoWeatherProvider(
            timeout_seconds=settings.realtime_weather_timeout_seconds,
            cache_ttl_seconds=settings.realtime_weather_cache_ttl_seconds,
        )
        if settings.realtime_weather_enabled
        else None
    )
    return ChatService(
        create_chat_model(settings),
        settings.llm_provider,
        model_version,
        weather_provider,
    )
