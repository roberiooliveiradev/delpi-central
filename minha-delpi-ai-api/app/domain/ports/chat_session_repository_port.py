from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chat_message import ChatMessage
from app.domain.entities.chat_session import ChatSession


class ChatSessionRepositoryPort(ABC):
    @abstractmethod
    def create_session(
        self,
        user_id: UUID,
        title: str | None,
        context: str | None,
    ) -> ChatSession:
        raise NotImplementedError

    @abstractmethod
    def list_sessions_by_user(self, user_id: UUID) -> list[ChatSession]:
        raise NotImplementedError

    @abstractmethod
    def get_session_by_id(self, session_id: UUID) -> ChatSession | None:
        raise NotImplementedError

    @abstractmethod
    def list_messages_by_session(self, session_id: UUID) -> list[ChatMessage]:
        raise NotImplementedError
