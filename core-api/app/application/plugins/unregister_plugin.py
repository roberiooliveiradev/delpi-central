# app/application/plugins/unregister_plugin.py

from dataclasses import dataclass
from app.infrastructure.db.models import App, AppManifest, AppRoute, Permission, AppVersion
from app.extensions.db import db

@dataclass
class UnregisterResult:
    success: bool
    error: str | None = None


class UnregisterPluginUseCase:

    def execute(self, plugin_id: str) -> UnregisterResult:
        app = App.query.filter_by(id=plugin_id).first()
        if not app:
            return UnregisterResult(False, "Plugin not found")

        # 🔒 Verifica dependências manualmente (compatível com JSON)
        all_manifests = AppManifest.query.all()

        dependents = []
        for m in all_manifests:
            deps = (m.manifest or {}).get("dependencies", [])
            if plugin_id in deps:
                dependents.append(m)

        if dependents:
            return UnregisterResult(False, "Other plugins depend on this plugin")

        # Remove tudo
        AppVersion.query.filter_by(app_id=plugin_id).delete()
        AppRoute.query.filter_by(app_id=plugin_id).delete()
        Permission.query.filter_by(module=plugin_id).delete()
        AppManifest.query.filter_by(app_id=plugin_id).delete()
        db.session.delete(app)

        db.session.commit()

        return UnregisterResult(True)