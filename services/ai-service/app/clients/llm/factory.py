from app.clients.llm.base import ChatModel
from app.clients.llm.gemini import GeminiChatModel
from app.clients.llm.groq import GroqChatModel
from app.clients.llm.local import LocalTransformersChatModel
from app.clients.llm.mock import MockChatModel
from app.core.config import Settings


def create_chat_model(settings: Settings) -> ChatModel:
    if settings.llm_provider == "gemini":
        return GeminiChatModel(settings)
    if settings.llm_provider == "groq":
        return GroqChatModel(settings)
    if settings.llm_provider == "local":
        return LocalTransformersChatModel(settings)
    return MockChatModel()
