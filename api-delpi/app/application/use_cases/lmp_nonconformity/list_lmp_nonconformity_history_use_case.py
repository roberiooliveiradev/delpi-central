from __future__ import annotations

from typing import Any, Protocol


class LmpNonconformityHistoryRepository(Protocol):
    def get_record(self, record_id: str) -> dict[str, Any] | None: ...

    def list_history(self, record_id: str) -> list[dict[str, Any]]: ...


class ListLmpNonconformityHistoryUseCase:
    def __init__(self, repository: LmpNonconformityHistoryRepository) -> None:
        self._repository = repository

    def execute(self, record_id: str) -> dict[str, Any] | None:
        if self._repository.get_record(record_id) is None:
            return None
        items = self._repository.list_history(record_id)
        return {"items": items, "total": len(items)}
