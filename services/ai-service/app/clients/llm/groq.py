import time
from collections.abc import Callable
from typing import Any

import httpx

from app.clients.llm.base import ChatMessage, GroqModelUnavailableError
from app.core.config import Settings


class GroqChatModel:
    """Synchronous Groq Chat Completions client for FastAPI thread-pool usage."""

    def __init__(
        self,
        settings: Settings,
        client: Any | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings
        self._client = client
        self._sleeper = sleeper

    def generate(self, messages: list[ChatMessage]) -> str:
        if not self.settings.groq_api_key:
            raise GroqModelUnavailableError(
                "Chưa cấu hình GROQ_API_KEY trong ai-service/.env."
            )

        payload = {
            "model": self.settings.groq_model,
            "messages": messages,
            "temperature": self.settings.groq_temperature,
            "max_completion_tokens": self.settings.groq_max_output_tokens,
        }
        attempts = max(1, self.settings.groq_max_retries + 1)

        for attempt in range(attempts):
            try:
                response = self._get_client().post(
                    f"{self.settings.groq_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "accept": "application/json",
                        "authorization": f"Bearer {self.settings.groq_api_key}",
                        "content-type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                reply = self._extract_reply(response.json())
                if not reply:
                    raise GroqModelUnavailableError(
                        "Groq không trả về nội dung văn bản. Vui lòng thử lại."
                    )
                return reply.strip()
            except GroqModelUnavailableError:
                raise
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code in {401, 403}:
                    raise GroqModelUnavailableError(
                        "Groq từ chối thông tin xác thực. Hãy kiểm tra GROQ_API_KEY."
                    ) from exc
                if status_code == 429:
                    message = "Groq đang giới hạn tần suất yêu cầu. Vui lòng thử lại sau."
                elif status_code >= 500:
                    message = "Groq đang tạm thời gián đoạn. Vui lòng thử lại sau."
                else:
                    raise GroqModelUnavailableError(
                        "Groq không thể xử lý yêu cầu hiện tại."
                    ) from exc
                if attempt == attempts - 1:
                    raise GroqModelUnavailableError(message) from exc
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt == attempts - 1:
                    raise GroqModelUnavailableError(
                        "Không thể kết nối Groq. Hãy kiểm tra mạng rồi thử lại."
                    ) from exc
            except httpx.HTTPError as exc:
                raise GroqModelUnavailableError(
                    "Groq không thể xử lý yêu cầu hiện tại."
                ) from exc
            except Exception as exc:
                raise GroqModelUnavailableError(
                    "Phản hồi Groq không hợp lệ. Vui lòng thử lại."
                ) from exc

            self._sleeper(0.3 * (3**attempt))

        raise GroqModelUnavailableError(
            "Groq đang tạm thời gián đoạn. Vui lòng thử lại sau."
        )

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = httpx.Client(timeout=self.settings.groq_timeout_seconds)
        return self._client

    @staticmethod
    def _extract_reply(payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return None
        message = first_choice.get("message")
        if not isinstance(message, dict):
            return None
        content = message.get("content")
        return content if isinstance(content, str) else None
