from typing import Any

from app.clients.llm.base import ChatMessage, GeminiModelUnavailableError
from app.core.config import Settings


class GeminiChatModel:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        self.settings = settings
        self._client = client

    def generate(self, messages: list[ChatMessage]) -> str:
        if not self.settings.gemini_api_key:
            raise GeminiModelUnavailableError(
                "Chưa cấu hình GEMINI_API_KEY trong services/ai-service/.env."
            )

        system_instruction = "\n\n".join(
            message["content"] for message in messages if message["role"] == "system"
        )
        contents = [
            {
                "role": "model" if message["role"] == "assistant" else "user",
                "parts": [{"text": message["content"]}],
            }
            for message in messages
            if message["role"] != "system"
        ]
        while contents and contents[0]["role"] == "model":
            contents.pop(0)

        try:
            client = self._client or self._create_client()
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=contents,
                config={
                    "system_instruction": system_instruction,
                    "temperature": self.settings.gemini_temperature,
                    "max_output_tokens": self.settings.gemini_max_output_tokens,
                    "thinking_config": {
                        "thinking_level": "low",
                        "include_thoughts": False,
                    },
                },
            )
            reply = self._extract_reply(response)
        except GeminiModelUnavailableError:
            raise
        except Exception as exc:
            raise GeminiModelUnavailableError(
                "Gemini đang không phản hồi. Kiểm tra API key, kết nối mạng và hạn mức API."
            ) from exc

        if not reply or not reply.strip():
            raise GeminiModelUnavailableError("Gemini không trả về nội dung văn bản.")
        return reply

    def _create_client(self) -> Any:
        try:
            from google import genai
        except ImportError as exc:
            raise GeminiModelUnavailableError(
                "Thiếu thư viện Gemini. Chạy: python -m pip install -e ."
            ) from exc

        self._client = genai.Client(api_key=self.settings.gemini_api_key)
        return self._client

    @staticmethod
    def _extract_reply(response: Any) -> str | None:
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            content = getattr(candidates[0], "content", None)
            parts = getattr(content, "parts", None) or []
            answer_parts = [
                part.text
                for part in parts
                if getattr(part, "text", None) and not getattr(part, "thought", False)
            ]
            if answer_parts:
                return "".join(answer_parts)
        return getattr(response, "text", None)
