# app/tests/integration/test_rollback_plugin.py

import json

from app.application.plugins.rollback_plugin_version import RollbackPluginVersionUseCase
from app.infrastructure.db.models import (
    App,
    AppManifest,
    AppRoute,
    Permission,
    AppVersion,
)
from app.extensions.db import db

def create_plugin_with_versions(app_id="rollback_test"):
    # 1️⃣ Criar App primeiro e COMMITAR
    app = App(
        id=app_id,
        name="Test",
        version="2.0.0",
        base_path=f"/{app_id}",
        type="microfrontend",
        active=True,
    )
    db.session.add(app)
    db.session.commit()  # 🔥 IMPORTANTE

    manifest_v1 = {
        "id": app_id,
        "version": "1.0.0",
        "routes": [{"path": f"/{app_id}", "label": "V1"}],
        "permissions": [{
            "code": f"{app_id}.resource.read",
            "name": "Read",
            "module": app_id
        }]
    }

    manifest_v2 = {
        "id": app_id,
        "version": "2.0.0",
        "routes": [{"path": f"/{app_id}/v2", "label": "V2"}],
        "permissions": [{
            "code": f"{app_id}.resource.write",
            "name": "Write",
            "module": app_id
        }]
    }

    db.session.add(AppManifest(
        app_id=app_id,
        manifest=manifest_v2,
        checksum="abc"
    ))

    db.session.add(AppVersion(
        app_id=app_id,
        version="1.0.0",
        manifest=manifest_v1,
        checksum="v1"
    ))

    db.session.add(AppVersion(
        app_id=app_id,
        version="2.0.0",
        manifest=manifest_v2,
        checksum="v2"
    ))

    db.session.commit()



def test_rollback_plugin_not_found(client):
    usecase = RollbackPluginVersionUseCase()
    result = usecase.execute("inexistent", "1.0.0")

    assert result.success is False
    assert result.errors[0]["code"] == "plugin.not_found"


def test_rollback_version_not_found(client):
    create_plugin_with_versions("rollback_missing")

    usecase = RollbackPluginVersionUseCase()
    result = usecase.execute("rollback_missing", "9.9.9")

    assert result.success is False
    assert result.errors[0]["code"] == "plugin.version_not_found"


def test_successful_rollback(client):
    plugin_id = "rollback_success"
    create_plugin_with_versions(plugin_id)

    usecase = RollbackPluginVersionUseCase()
    result = usecase.execute(plugin_id, "1.0.0")

    assert result.success is True

    app = App.query.get(plugin_id)
    assert app.version == "1.0.0"

    routes = AppRoute.query.filter_by(app_id=plugin_id).all()
    assert len(routes) == 1
    assert routes[0].path == f"/{plugin_id}"

    perms = Permission.query.filter_by(module=plugin_id).all()
    assert len(perms) == 1
    assert perms[0].code.endswith(".read")