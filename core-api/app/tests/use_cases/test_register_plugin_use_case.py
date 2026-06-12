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

    def create(self, data, **kwargs):
        self.created = True

    def update_version(self, plugin_id, version, **kwargs):
        pass


class FakePluginRoutes:
    def __init__(self):
        self.last_bulk_create: list | None = None

    def bulk_create(self, routes):
        self.last_bulk_create = routes


class FakeUoW:
    def __init__(self, exists=False):
        self.plugins = FakePlugins(exists)
        self.plugin_manifests = SimpleNamespace(save=lambda *a, **k: None)
        self.plugin_versions = SimpleNamespace(
            create=lambda *a, **k: None,
            exists=lambda *a, **k: False,
        )
        self.plugin_permissions = SimpleNamespace(bulk_create=lambda *a, **k: None)
        self.plugin_routes = FakePluginRoutes()
        self.committed = False
        self.rolled_back = False
        self.events: list = []

    def collect_event(self, event):
        self.events.append(event)

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
        "basePath": "/apps/crm",
        "routes": [],
        "permissions": [],
    }


def test_register_success():
    uow = FakeUoW(exists=False)
    use_case = RegisterPluginUseCase(uow, FakeValidator(True))

    result = use_case.execute(base_manifest())

    assert result.success
    assert uow.plugins.created


def test_register_already_exists():
    uow = FakeUoW(exists=True)
    uow.plugin_versions.exists = lambda plugin_id, version: True
    use_case = RegisterPluginUseCase(uow, FakeValidator(True))

    result = use_case.execute(base_manifest())

    assert not result.success
    assert result.errors[0]["code"] == "plugin.version_already_exists"


def test_register_validation_error():
    error = SimpleNamespace(code="invalid", message="bad", path="id")
    use_case = RegisterPluginUseCase(FakeUoW(), FakeValidator(False, [error]))

    result = use_case.execute(base_manifest())

    assert not result.success
    assert result.errors[0]["code"] == "invalid"


def test_register_first_create_maps_show_in_menu_from_manifest():
    uow = FakeUoW(exists=False)
    use_case = RegisterPluginUseCase(uow, FakeValidator(True))

    manifest = {
        **base_manifest(),
        "basePath": "/apps/demo",
        "routes": [
            {
                "path": "/apps/demo",
                "label": "Demo",
                "permission": "demo.view",
                "showInMenu": True,
            },
            {
                "path": "/apps/demo/hidden",
                "label": "Hidden",
                "permission": "demo.view",
                "showInMenu": False,
            },
        ],
    }

    result = use_case.execute(manifest)

    assert result.success
    assert uow.plugin_routes.last_bulk_create == [
        {
            "app_id": "crm",
            "path": "/apps/demo",
            "label": "Demo",
            "icon": None,
            "permission": "demo.view",
            "order": 0,
            "show_in_menu": True,
        },
        {
            "app_id": "crm",
            "path": "/apps/demo/hidden",
            "label": "Hidden",
            "icon": None,
            "permission": "demo.view",
            "order": 0,
            "show_in_menu": False,
        },
    ]