# app/application/use_cases/list_plugin_versions_use_case.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class ListPluginVersionsResult:
    success: bool
    versions: List[Dict[str, Any]]
    errors: Optional[List[Dict[str, Any]]] = None


class ListPluginVersionsUseCase:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str) -> ListPluginVersionsResult:
        try:
            app = self._uow.plugin_repo.get_by_id(plugin_id)
            if not app:
                return ListPluginVersionsResult(
                    success=False,
                    versions=[],
                    errors=[{"code": "plugin.not_found", "message": "Plugin not found", "path": "_global"}],
                )

            versions = self._uow.version_repo.list_versions(plugin_id)
            return ListPluginVersionsResult(success=True, versions=versions, errors=None)

        except Exception as e:
            return ListPluginVersionsResult(
                success=False,
                versions=[],
                errors=[{"code": "plugin.list_versions_failed", "message": str(e), "path": "_global"}],
            )