from abc import ABC, abstractmethod
from uuid import UUID


class AuditRepositoryPort(ABC):
    @abstractmethod
    def log(
        self,
        user_id: UUID | None,
        action: str,
        prompt_hash: str | None = None,
        context: str | None = None,
        tool_calls: list | None = None,
        metadata: dict | None = None,
    ) -> None:
        raise NotImplementedError
