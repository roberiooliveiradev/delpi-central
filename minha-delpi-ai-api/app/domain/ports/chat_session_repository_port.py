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
        project_id: UUID | None = None,
        agent_key: str | None = None,
    ) -> ChatSession:
        raise NotImplementedError

    @abstractmethod
    def list_sessions_by_user(
        self,
        user_id: UUID,
        archived: bool = False,
    ) -> list[ChatSession]:
        raise NotImplementedError


    @abstractmethod
    def rename_session(
        self,
        session_id: UUID,
        user_id: UUID,
        title: str,
    ) -> ChatSession | None:
        raise NotImplementedError

    @abstractmethod
    def update_session_agent_key(
        self,
        session_id: UUID,
        user_id: UUID,
        agent_key: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_session_by_id(self, session_id: UUID) -> ChatSession | None:
        raise NotImplementedError

    @abstractmethod
    def list_messages_by_session(self, session_id: UUID) -> list[ChatMessage]:
        raise NotImplementedError

    @abstractmethod
    def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_session_pinned(
        self,
        session_id: UUID,
        user_id: UUID,
        pinned: bool,
    ) -> ChatSession | None:
        raise NotImplementedError

    @abstractmethod
    def set_session_archived(
        self,
        session_id: UUID,
        user_id: UUID,
        archived: bool,
    ) -> ChatSession | None:
        raise NotImplementedError

    @abstractmethod
    def update_user_message(
        self,
        message_id: UUID,
        user_id: UUID,
        content: str,
        metadata_patch: dict | None = None,
    ) -> ChatMessage | None:
        raise NotImplementedError

    @abstractmethod
    def delete_messages_after(
        self,
        *,
        session_id: UUID,
        message_id: UUID,
        user_id: UUID,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_user_message_for_user(
        self,
        *,
        message_id: UUID,
        user_id: UUID,
        session_id: UUID | None = None,
    ) -> ChatMessage | None:
        raise NotImplementedError

    @abstractmethod
    def create_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> ChatMessage:
        raise NotImplementedError

    @abstractmethod
    def update_assistant_message(
        self,
        message_id: UUID,
        content: str,
        metadata: dict | None = None,
    ) -> ChatMessage | None:
        raise NotImplementedError
