# app/tests/use_cases/test_register_plugin_use_case.py

from types import SimpleNamespace
from app.application.use_cases.register_plugin_use_case import RegisterPluginUseCase


class FakeValidator:
    def __init__(self, is_valid=True, errors=None):
        self._is_valid = is_valid
        self._errors = errors or []

    def validate(self, manifest):
        return SimpleNamespace(is_valid=self._is_valid, errors=self._errors)


class FakePlugins:
    def __init__(self, exists=False):
        self._exists = exists
        self.created = False

    def get_by_id(self, pid):
        return {"id": pid} if self._exists else None

    def create(self, data):
        self.created = True


class FakeUoW:
    def __init__(self, exists=False):
        self.plugins = FakePlugins(exists)
        self.plugin_manifests = SimpleNamespace(save=lambda *a, **k: None)
        self.plugin_versions = SimpleNamespace(create=lambda *a, **k: None)
        self.plugin_permissions = SimpleNamespace(bulk_create=lambda *a, **k: None)
        self.plugin_routes = SimpleNamespace(bulk_create=lambda *a, **k: None)
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def base_manifest():
    return {
        "id": "crm",
        "name": "CRM",
        "version": "1.0.0",
        "type": "microfrontend",
        "routes": [],
        "permissions": [],
    }


def test_register_success():
    uow = FakeUoW(exists=False)
    use_case = RegisterPluginUseCase(uow, FakeValidator(True))

    result = use_case.execute(base_manifest())

    assert result.success
    assert uow.plugins.created
    assert uow.committed


def test_register_already_exists():
    uow = FakeUoW(exists=True)
    use_case = RegisterPluginUseCase(uow, FakeValidator(True))

    result = use_case.execute(base_manifest())

    assert not result.success
    assert result.errors[0]["code"] == "plugin.already_exists"


def test_register_validation_error():
    error = SimpleNamespace(code="invalid", message="bad", path="id")
    use_case = RegisterPluginUseCase(FakeUoW(), FakeValidator(False, [error]))

    result = use_case.execute(base_manifest())

    assert not result.success
    assert result.errors[0]["code"] == "invalid"