# app/application/plugins/unregister_plugin.py

from dataclasses import dataclass
from app.infrastructure.db.models import App, AppManifest, AppRoute, Permission, AppVersion
from app.extensions.db import db

@dataclass
class UnregisterResult:
    success: bool
    error: str | None = None


class UnregisterPluginUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str):

        try:
            app = self._uow.app_repo.get_by_id(plugin_id)
            if not app:
                return UnregisterResult(False, "Plugin not found")

            self._uow.app_version_repo.delete_by_app(plugin_id)
            self._uow.route_repo.delete_by_app(plugin_id)
            self._uow.permission_repo.delete_by_module(plugin_id)
            self._uow.manifest_repo.delete(plugin_id)
            self._uow.app_repo.delete(plugin_id)

            self._uow.commit()

            return UnregisterResult(True)

        except Exception:
            self._uow.rollback()
            raise