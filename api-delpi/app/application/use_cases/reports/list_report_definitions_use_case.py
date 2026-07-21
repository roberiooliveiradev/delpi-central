from __future__ import annotations

from typing import Any, Protocol


class ReportsDefinitionsRepository(Protocol):
    def list_definitions(self) -> list[dict[str, Any]]: ...


class ListReportDefinitionsUseCase:
    def __init__(self, repository: ReportsDefinitionsRepository) -> None:
        self._repository = repository

    def execute(self) -> dict[str, Any]:
        items = self._repository.list_definitions()
        return {"items": items, "total": len(items)}
