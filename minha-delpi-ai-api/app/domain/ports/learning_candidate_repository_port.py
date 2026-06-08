from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class LearningCandidateRepositoryPort(ABC):
    @abstractmethod
    def find_active_duplicate(
        self,
        *,
        candidate_type: str,
        term: str,
        scope: str,
        project_id: UUID | None = None,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        *,
        candidate_type: str,
        input_text: str,
        term: str | None = None,
        proposed_rule: str | None = None,
        proposed_meaning: str | None = None,
        evidence: dict | None = None,
        confidence: float | None = None,
        evidence_count: int = 1,
        risk_level: str = "low",
        scope: str = "global",
        project_id: UUID | None = None,
        status: str = "pending",
        source: str = "auto",
        created_by: UUID | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def bump_evidence(
        self,
        candidate_id: int,
        *,
        confidence: float | None = None,
        example: str | None = None,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_candidates(
        self,
        *,
        status: str | None = None,
        candidate_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def summary(self, *, since: datetime | None = None) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get(self, candidate_id: int) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def update_status(
        self,
        candidate_id: int,
        *,
        status: str,
        reviewer_id: UUID | None = None,
        promoted_term_id: int | None = None,
    ) -> dict | None:
        raise NotImplementedError
