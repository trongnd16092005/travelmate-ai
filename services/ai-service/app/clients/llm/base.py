from typing import Protocol

ChatMessage = dict[str, str]


class ChatModel(Protocol):
    def generate(self, messages: list[ChatMessage]) -> str:
        """Generate one assistant response from a chat message list."""


class LocalModelUnavailableError(RuntimeError):
    """Raised when the local model cannot be loaded or used."""
