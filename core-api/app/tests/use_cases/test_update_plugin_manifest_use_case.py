# app/tests/use_cases/test_update_plugin_manifest_use_case.py

from types import SimpleNamespace

from app.application.use_cases.update_plugin_manifest_use_case import UpdatePluginManifestUseCase


class FakeValidator:
    def __init__(self, is_valid=True):
        self._is_valid = is_valid

    def validate(self, manifest):
        return SimpleNamespace(is_valid=self._is_valid, errors=[])


class FakePlugins:
    def __init__(self, plugin):
        self._plugin = plugin
        self.last_update_metadata = None

    def get_by_id(self, pid):
        return self._plugin

    def update_metadata(self, plugin_id, **kwargs):
        self.last_update_metadata = {"plugin_id": plugin_id, **kwargs}


class FakeUoW:
    def __init__(self, plugin=None):
        self.plugins = FakePlugins(plugin)
        self.permissions = SimpleNamespace(list_by_module=lambda module: [])
        self.plugin_manifests = SimpleNamespace(save=lambda *a, **k: None)
        self.plugin_routes = SimpleNamespace(
            list_by_app=lambda app_id: [],
            update_by_app_and_path=lambda *a, **k: None,
        )
        self.events = []

    def collect_event(self, event):
        self.events.append(event)


def test_update_manifest_success_syncs_identity_via_canonical_helper():
    plugin = SimpleNamespace(
        version="1.0.0",
        name="CRM",
        base_path="/apps/crm",
    )
    uow = FakeUoW(plugin)

    manifest = {
        "id": "crm",
        "version": "1.0.0",
        "name": "CRM Updated",
        "description": "nova",
        "icon": "briefcase-business",
        "basePath": "/apps/crm",
        "permissions": [],
        "routes": [],
    }

    use_case = UpdatePluginManifestUseCase(uow, FakeValidator(True))
    result = use_case.execute("crm", manifest)

    assert result.success
    assert uow.plugins.last_update_metadata == {
        "plugin_id": "crm",
        "name": "CRM Updated",
        "description": "nova",
        "icon": "briefcase-business",
        "app_type": None,
        "base_path": None,
        "actor_user_id": None,
        "actor_name": None,
    }
    assert len(uow.events) == 1


def test_update_manifest_id_mismatch():
    plugin = SimpleNamespace(version="1.0.0", name="CRM", base_path="/apps/crm")
    uow = FakeUoW(plugin)

    manifest = {"id": "wrong", "version": "1.0.0"}

    use_case = UpdatePluginManifestUseCase(uow, FakeValidator(True))
    result = use_case.execute("crm", manifest)

    assert not result.success
    assert result.errors[0]["code"] == "plugin.id_mismatch"
