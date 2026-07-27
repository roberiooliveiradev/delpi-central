from __future__ import annotations

from typing import Any, Protocol


class LmpNonconformityGetRepository(Protocol):
    def get_record(self, record_id: str) -> dict[str, Any] | None: ...


class GetLmpNonconformityUseCase:
    def __init__(self, repository: LmpNonconformityGetRepository) -> None:
        self._repository = repository

    def execute(self, record_id: str) -> dict[str, Any] | None:
        return self._repository.get_record(record_id)
