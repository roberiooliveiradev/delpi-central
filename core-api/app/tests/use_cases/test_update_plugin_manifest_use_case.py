# app/tests/use_cases/test_update_plugin_manifest_use_case.py

from types import SimpleNamespace
from app.application.use_cases.update_plugin_manifest_use_case import UpdatePluginManifestUseCase


class FakeValidator:
    def __init__(self, is_valid=True):
        self._is_valid = is_valid

    def validate(self, manifest):
        return SimpleNamespace(is_valid=self._is_valid, errors=[])


class FakeUoW:
    def __init__(self, plugin=None):
        self.plugins = SimpleNamespace(
            get_by_id=lambda pid: plugin,
            update_metadata=lambda *a, **k: None,
        )
        self.plugin_manifests = SimpleNamespace(save=lambda *a, **k: None)
        self.plugin_routes = SimpleNamespace(update_by_app_and_path=lambda *a, **k: None)
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_update_manifest_success():
    plugin = {"version": "1.0.0", "name": "CRM"}
    uow = FakeUoW(plugin)

    manifest = {
        "id": "crm",
        "version": "1.0.0",
        "name": "CRM Updated",
        "routes": [],
    }

    use_case = UpdatePluginManifestUseCase(uow, FakeValidator(True))
    result = use_case.execute("crm", manifest)

    assert result.success
    assert uow.committed


def test_update_manifest_id_mismatch():
    plugin = {"version": "1.0.0", "name": "CRM"}
    uow = FakeUoW(plugin)

    manifest = {"id": "wrong", "version": "1.0.0"}

    use_case = UpdatePluginManifestUseCase(uow, FakeValidator(True))
    result = use_case.execute("crm", manifest)

    assert not result.success
    assert result.errors[0]["code"] == "plugin.id_mismatch"