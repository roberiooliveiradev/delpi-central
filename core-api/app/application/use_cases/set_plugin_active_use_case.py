# app/application/use_cases/set_plugin_active_use_case.py

from dataclasses import dataclass
from typing import Dict, List
from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class SetPluginActiveResult:
    success: bool
    errors: List[Dict[str, str]]


class SetPluginActiveUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str, active: bool) -> SetPluginActiveResult:

        plugin = self._uow.plugins.get_by_id(plugin_id)
        if not plugin:
            return SetPluginActiveResult(
                success=False,
                errors=[{
                    "code": "plugin.not_found",
                    "message": "Plugin not found",
                    "path": "_global"
                }]
            )

        try:
            plugin.active = active
            self._uow.commit()

            return SetPluginActiveResult(success=True, errors=[])

        except Exception as e:
            self._uow.rollback()
            return SetPluginActiveResult(
                success=False,
                errors=[{
                    "code": "plugin.activation_failed",
                    "message": str(e),
                    "path": "_global"
                }]
            )