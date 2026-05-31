from abc import ABC, abstractmethod
from uuid import UUID


class ChatSessionMemoryRepositoryPort(ABC):
    @abstractmethod
    def load_active_overlay(self, session_id: UUID) -> dict:
        """Retorna ``lastEntities`` e ``behaviorInstructions`` ativos da sessão."""
        raise NotImplementedError

    @abstractmethod
    def sync_from_snapshot(
        self,
        session_id: UUID,
        snapshot: dict,
        *,
        source_message_id: UUID | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def deactivate_all(self, session_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    def expire_stale(self, *, older_than_days: int = 30) -> int:
        raise NotImplementedError
