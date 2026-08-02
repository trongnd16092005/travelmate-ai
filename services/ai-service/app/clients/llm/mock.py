from app.clients.llm.base import ChatMessage


class MockChatModel:
    def generate(self, messages: list[ChatMessage]) -> str:
        user_message = messages[-1]["content"]
        return (
            "Mình đã nhận câu hỏi về chuyến đi: "
            f"\"{user_message}\". Đây là phản hồi mẫu; hãy bật LLM_PROVIDER=local "
            "sau khi đã tải mô hình để nhận tư vấn từ TravelMate AI."
        )
