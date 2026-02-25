# app/application/plugins/rollback_plugin_version.py

from dataclasses import dataclass
from typing import List

from app.application.plugins.ports import UnitOfWork


@dataclass
class RollbackResult:
    success: bool
    errors: List[dict]


class RollbackPluginVersionUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str, target_version: str) -> RollbackResult:

        try:
            app = self._uow.app_repo.get_by_id(plugin_id)
            if not app:
                return RollbackResult(False, [{
                    "code": "plugin.not_found",
                    "message": "Plugin not found",
                    "path": "_global",
                }])

            version_row = self._uow.app_version_repo.get(plugin_id, target_version)
            if not version_row:
                return RollbackResult(False, [{
                    "code": "plugin.version_not_found",
                    "message": "Target version not found in history",
                    "path": "version",
                }])

            manifest = version_row["manifest"]

            # Atualiza versão ativa
            self._uow.app_repo.update_version(plugin_id, target_version)

            # Atualiza manifest atual
            self._uow.manifest_repo.save(
                plugin_id,
                manifest,
                version_row["checksum"],
            )

            # Sincroniza rotas
            self._uow.route_repo.delete_by_app(plugin_id)
            self._uow.route_repo.bulk_create([
                {
                    "app_id": plugin_id,
                    "path": r["path"],
                    "label": r.get("label"),
                    "icon": r.get("icon"),
                    "permission": r.get("permission"),
                    "show_in_menu": r.get("showInMenu", True),
                    "order": r.get("order", 0),
                }
                for r in manifest.get("routes", [])
            ])

            # Sincroniza permissões
            self._uow.permission_repo.delete_by_module(plugin_id)
            self._uow.permission_repo.bulk_create(manifest.get("permissions", []))

            self._uow.commit()

            return RollbackResult(True, [])

        except Exception:
            self._uow.rollback()
            raise