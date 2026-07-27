from __future__ import annotations

from typing import Any, Protocol


class LmpNonconformityDeleteRepository(Protocol):
    def delete_record(self, record_id: str) -> bool: ...


class DeleteLmpNonconformityUseCase:
    def __init__(self, repository: LmpNonconformityDeleteRepository) -> None:
        self._repository = repository

    def execute(self, record_id: str) -> bool:
        return self._repository.delete_record(record_id)
