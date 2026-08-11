from typing import Protocol

ChatMessage = dict[str, str]


class ChatModel(Protocol):
    def generate(self, messages: list[ChatMessage]) -> str:
        """Generate one assistant response from a chat message list."""


class ChatModelUnavailableError(RuntimeError):
    """Raised when the configured chat model cannot answer a request."""


class LocalModelUnavailableError(ChatModelUnavailableError):
    """Raised when the local model cannot be loaded or used."""


class GeminiModelUnavailableError(ChatModelUnavailableError):
    """Raised when Gemini is not configured or its API request fails."""


class GroqModelUnavailableError(ChatModelUnavailableError):
    """Raised when Groq is not configured or its API request fails."""
