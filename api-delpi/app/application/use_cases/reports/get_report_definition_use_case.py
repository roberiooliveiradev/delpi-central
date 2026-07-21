from __future__ import annotations

from typing import Any, Protocol


class ReportsGetDefinitionRepository(Protocol):
    def get_definition(self, definition_id: str) -> dict[str, Any] | None: ...


class GetReportDefinitionUseCase:
    def __init__(self, repository: ReportsGetDefinitionRepository) -> None:
        self._repository = repository

    def execute(self, definition_id: str) -> dict[str, Any] | None:
        return self._repository.get_definition(definition_id)
