from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ResponseEvaluationQuery:
    limit: int = 20
    offset: int = 0
    verdict: str | None = None
    min_score: int | None = None
    max_score: int | None = None
    search: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class ResponseEvaluationRepositoryPort(ABC):
    @abstractmethod
    def upsert_evaluation(
        self,
        *,
        message_id: UUID,
        session_id: UUID,
        evaluator_user_id: UUID,
        score: int,
        verdict: str,
        comment: str | None,
        suggestions: dict | None,
        metadata: dict | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_evaluation_by_message_id(self, message_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_evaluations(self, query: ResponseEvaluationQuery) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def get_summary(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_assistant_message_candidates(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def get_assistant_message_context(self, message_id: UUID) -> dict | None:
        raise NotImplementedError
