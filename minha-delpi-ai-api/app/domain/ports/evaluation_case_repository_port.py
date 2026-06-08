from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class EvaluationCaseRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        *,
        category: str,
        input_text: str,
        expected_intent: str | None = None,
        expected_answer: str | None = None,
        expected_normalized: str | None = None,
        must_not_use_tools: bool = False,
        must_not_use_rag: bool = False,
        source_feedback_id: int | None = None,
        linked_candidate_id: int | None = None,
        created_by: UUID | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get(self, case_id: int) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_cases(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def list_active(self, *, categories: tuple[str, ...] | None = None) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def update_run_result(
        self,
        case_id: int,
        *,
        passed: bool,
        failure_reason: str | None = None,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def set_status(self, case_id: int, *, status: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def find_duplicate_input(self, *, input_text: str, category: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def summary(self) -> dict:
        raise NotImplementedError
