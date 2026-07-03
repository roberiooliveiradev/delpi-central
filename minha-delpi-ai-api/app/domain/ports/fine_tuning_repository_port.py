from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class FineTuningRepositoryPort(ABC):
    @abstractmethod
    def create_dataset(
        self,
        *,
        name: str,
        description: str | None = None,
        target_model: str = "intent_classifier",
        metadata: dict | None = None,
        created_by: UUID | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_dataset(self, dataset_id: int) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_datasets(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def approve_dataset(self, dataset_id: int, *, approved_by: UUID | None = None) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def create_sample(
        self,
        *,
        messages_json: list,
        category: str = "routing",
        source: str,
        source_ref: str | None = None,
        intent_label: str | None = None,
        quality_score: float | None = None,
        anonymized: bool = False,
        risk_level: str | None = None,
        dataset_id: int | None = None,
        created_by: UUID | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def find_sample_by_source(self, *, source: str, source_ref: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def get_sample(self, sample_id: int) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_samples(
        self,
        *,
        status: str | None = None,
        dataset_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def list_approved_for_dataset(self, dataset_id: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def update_sample_status(
        self,
        sample_id: int,
        *,
        status: str,
        reviewer_id: UUID | None = None,
        dataset_id: int | None = None,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def assign_samples_to_dataset(self, *, dataset_id: int, sample_ids: list[int]) -> int:
        raise NotImplementedError

    @abstractmethod
    def create_run(
        self,
        *,
        dataset_id: int,
        target_model: str,
        created_by: UUID | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_run(self, run_id: int) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def update_run(
        self,
        run_id: int,
        *,
        status: str | None = None,
        export_stats: dict | None = None,
        metrics: dict | None = None,
        error_message: str | None = None,
        active_deploy: bool | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def deactivate_deploys(self, *, target_model: str, except_run_id: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_runs(self, *, dataset_id: int | None = None, limit: int = 20) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def summary(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_active_deployed_chat_model(self) -> str | None:
        raise NotImplementedError

    def get_active_deployed_ollama_model(self) -> str | None:
        return self.get_active_deployed_chat_model()
