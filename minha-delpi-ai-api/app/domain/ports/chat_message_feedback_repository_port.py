from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class ChatMessageFeedbackRepositoryPort(ABC):
    @abstractmethod
    def upsert_feedback(
        self,
        *,
        message_id: UUID,
        user_id: UUID,
        rating: int,
        reason: str | None = None,
        comment: str | None = None,
        context_metadata: dict | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def delete_feedback(self, *, message_id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_feedback_for_user(
        self,
        *,
        message_id: UUID,
        user_id: UUID,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_feedback_by_message_ids(
        self,
        *,
        message_ids: list[UUID],
        user_id: UUID,
    ) -> dict[str, dict]:
        raise NotImplementedError

    @abstractmethod
    def get_assistant_message(self, message_id: UUID) -> dict | None:
        """Retorna ``id``, ``metadata`` e ``content`` da mensagem assistente."""
        raise NotImplementedError

    @abstractmethod
    def get_user_question_for_assistant(self, message_id: UUID) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def get_message_session_id(self, message_id: UUID) -> UUID | None:
        raise NotImplementedError

    @abstractmethod
    def list_feedback_since(self, *, since: datetime) -> list[dict]:
        raise NotImplementedError
