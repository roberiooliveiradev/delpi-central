from __future__ import annotations

from typing import Protocol


class CaseSimilarityIndexRepository(Protocol):
    def sync_case_similarity_index(self, plan_id: str) -> None: ...


class SyncCaseSimilarityIndexUseCase:
    def __init__(self, repository: CaseSimilarityIndexRepository) -> None:
        self._repository = repository

    def execute(self, plan_id: str) -> None:
        self._repository.sync_case_similarity_index(plan_id)
