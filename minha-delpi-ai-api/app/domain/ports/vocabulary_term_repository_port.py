from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class VocabularyTermRepositoryPort(ABC):
    @abstractmethod
    def upsert_term(
        self,
        *,
        term: str,
        normalized_term: str,
        meaning: str | None = None,
        type: str = "typo",
        scope: str = "global",
        project_id: UUID | None = None,
        source: str = "promotion",
        confidence: float | None = None,
        approved: bool = False,
        active: bool = True,
        created_by: UUID | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_terms(
        self,
        *,
        scope: str | None = None,
        approved: bool | None = None,
        type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def list_active_normalization_rules(
        self,
        *,
        scopes: tuple[str, ...] = ("global",),
        max_rules: int = 500,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_active_definitions(
        self,
        *,
        scopes: tuple[str, ...] = ("global",),
        project_id: UUID | None = None,
        max_terms: int = 300,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def find_definition_by_term(
        self,
        *,
        normalized_term: str,
        scopes: tuple[str, ...] = ("global",),
        project_id: UUID | None = None,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_top_typo_rules(self, *, limit: int = 8) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def summary(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get(self, term_id: int) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def set_active(self, term_id: int, *, active: bool) -> dict | None:
        raise NotImplementedError
