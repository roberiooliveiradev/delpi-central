# app/application/use_cases/get_plugin_version_use_case.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class GetPluginVersionResult:
    success: bool
    version: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None


class GetPluginVersionUseCase:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str, version: str) -> GetPluginVersionResult:
        plugin = self._uow.plugins.get_by_id(plugin_id)
        if not plugin:
            return GetPluginVersionResult(
                success=False,
                errors=[
                    {
                        "code": "plugin.not_found",
                        "message": "Plugin não encontrado",
                        "path": "_global",
                    }
                ],
            )

        row = self._uow.plugin_versions.get_version(plugin_id, version)
        if not row:
            return GetPluginVersionResult(
                success=False,
                errors=[
                    {
                        "code": "plugin.version_not_found",
                        "message": "Versão alvo não encontrada no histórico",
                        "path": "version",
                    }
                ],
            )

        return GetPluginVersionResult(success=True, version=row, errors=None)
