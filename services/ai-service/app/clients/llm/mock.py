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
        destination_match = re.search(r"Điểm đến:\s*(.+)", user_prompt)
        duration_days = int(duration_match.group(1)) if duration_match else 1
        destination = destination_match.group(1).strip() if destination_match else "điểm đến"
        return json.dumps(
            {
                "summary": f"Bản mẫu {duration_days} ngày tại {destination}.",
                "assumptions": ["Đây là dữ liệu mock để kiểm tra giao diện."],
                "days": [
                    {
                        "day": day,
                        "title": f"Khám phá {destination} ngày {day}",
                        "activities": [
                            {
                                "period": "morning",
                                "title": "Khám phá địa điểm phù hợp",
                                "placeName": destination,
                                "notes": "Bật Gemini hoặc Qwen local để nhận gợi ý thực tế.",
                            }
                        ],
                    }
                    for day in range(1, duration_days + 1)
                ],
            },
            ensure_ascii=False,
        )
