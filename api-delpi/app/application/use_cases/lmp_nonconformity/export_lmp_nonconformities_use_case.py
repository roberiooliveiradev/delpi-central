from __future__ import annotations

from typing import Any, Protocol


class LmpNonconformityExportRepository(Protocol):
    def export_records(self) -> list[dict[str, Any]]: ...


class ExportLmpNonconformitiesUseCase:
    def __init__(self, repository: LmpNonconformityExportRepository) -> None:
        self._repository = repository

    def execute(self) -> list[dict[str, Any]]:
        return self._repository.export_records()
