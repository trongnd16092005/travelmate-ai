import json
import re

from app.clients.llm.base import ChatMessage


class MockChatModel:
    def generate(self, messages: list[ChatMessage]) -> str:
        if messages and "[ITINERARY_JSON]" in messages[0]["content"]:
            return self._generate_itinerary(messages[-1]["content"])
        user_message = messages[-1]["content"]
        return (
            "Mình đã nhận câu hỏi về chuyến đi: "
            f'"{user_message}". Đây là phản hồi mẫu; hãy bật provider Gemini '
            "hoặc mô hình local để nhận tư vấn từ TravelMate AI."
        )

    @staticmethod
    def _generate_itinerary(user_prompt: str) -> str:
        duration_match = re.search(r"Số ngày:\s*(\d+)", user_prompt)
        duration_days = int(duration_match.group(1)) if duration_match else 1
        allowed_place_ids = re.findall(r"^- ([^|\n]+)\s*\|", user_prompt, flags=re.MULTILINE)
        return json.dumps(
            {
                "days": [
                    {
                        "day": day,
                        "activities": [
                            {
                                "period": "morning",
                                "kind": "visit" if allowed_place_ids else "free_time",
                                "placeId": (
                                    allowed_place_ids[(day - 1) % len(allowed_place_ids)].strip()
                                    if allowed_place_ids
                                    else None
                                ),
                            }
                        ],
                    }
                    for day in range(1, duration_days + 1)
                ],
            },
            ensure_ascii=False,
        )
