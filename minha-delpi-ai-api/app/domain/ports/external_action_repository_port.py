from __future__ import annotations

from abc import ABC, abstractmethod


class ExternalActionRepositoryPort(ABC):
    @abstractmethod
    def create_provider(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_providers(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_provider_by_key(self, provider_key: str):
        raise NotImplementedError

    @abstractmethod
    def update_provider(self, provider_key: str, payload: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def get_provider_details(self, provider_key: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def import_schema_from_json(
        self,
        provider_key: str,
        schema_json: dict,
        source_type: str,
        source_url: str | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def import_schema_from_url(self, provider_key: str, timeout: int = 20) -> dict:
        raise NotImplementedError

    @abstractmethod
    def find_candidate_actions(
        self,
        query: str,
        limit: int = 8,
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def search_similar_actions(
        self,
        embedding: list[float],
        *,
        allowed_action_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def backfill_action_embeddings(self, *, provider_key: str | None = None) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_action_for_execution(self, action_id: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_actions(self, provider_key: str | None = None) -> list[dict]:
        raise NotImplementedError
