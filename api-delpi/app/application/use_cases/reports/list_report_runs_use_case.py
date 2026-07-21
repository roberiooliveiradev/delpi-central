from __future__ import annotations

from typing import Any, Protocol


class ReportsRunsRepository(Protocol):
    def list_runs(
        self,
        *,
        definition_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]: ...


class ListReportRunsUseCase:
    def __init__(self, repository: ReportsRunsRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        definition_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        items = self._repository.list_runs(
            definition_id=definition_id,
            limit=limit,
        )
        return {"items": items, "total": len(items)}
