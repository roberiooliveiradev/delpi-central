# app/tests/integration/test_unregister_plugin.py

from app.application.plugins.unregister_plugin import UnregisterPluginUseCase
from app.infrastructure.db.models import App, AppManifest, AppVersion
from app.extensions.db import db


def create_basic_plugin(app_id="unreg_test"):
    app = App(
        id=app_id,
        name="Test",
        version="1.0.0",
        base_path=f"/{app_id}",
        type="microfrontend",
        active=True,
    )
    db.session.add(app)
    db.session.commit()
    return app


def test_unregister_plugin_not_found(client):
    usecase = UnregisterPluginUseCase()
    result = usecase.execute("not_exists")

    assert result.success is False
    assert result.error == "Plugin not found"


def test_unregister_with_dependencies_blocked(client):
    create_basic_plugin("base_plugin")

    # cria dependente
    create_basic_plugin("dependent_plugin")

    db.session.add(AppManifest(
        app_id="dependent_plugin",
        manifest={
            "id": "dependent_plugin",
            "dependencies": ["base_plugin"]
        },
        checksum="x"
    ))
    db.session.commit()

    usecase = UnregisterPluginUseCase()
    result = usecase.execute("base_plugin")

    assert result.success is False
    assert result.error == "Other plugins depend on this plugin"


def test_unregister_success(client):
    create_basic_plugin("remove_me")

    usecase = UnregisterPluginUseCase()
    result = usecase.execute("remove_me")

    assert result.success is True

    assert App.query.get("remove_me") is None