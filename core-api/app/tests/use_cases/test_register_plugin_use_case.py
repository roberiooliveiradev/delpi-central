# app/tests/use_cases/test_register_plugin_use_case.py

from types import SimpleNamespace
from uuid import uuid4

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
        self.last_create = None
        self.last_update_version = None
        self.last_update_metadata = None

    def get_by_id(self, pid):
        return SimpleNamespace(id=pid, name="CRM antigo") if self._exists else None

    def create(self, data, **kwargs):
        self.created = True
        self.last_create = data

    def update_version(self, plugin_id, version, **kwargs):
        self.last_update_version = {"plugin_id": plugin_id, "version": version, **kwargs}

    def update_metadata(self, plugin_id, **kwargs):
        self.last_update_metadata = {"plugin_id": plugin_id, **kwargs}


class FakePluginRoutes:
    def __init__(self):
        self.last_bulk_create: list | None = None
        self.deleted_app: str | None = None

    def bulk_create(self, routes):
        self.last_bulk_create = routes

    def delete_by_app(self, plugin_id):
        self.deleted_app = plugin_id


class FakePluginPermissions:
    """In-memory sync that preserves UUID for kept codes."""

    def __init__(self):
        self.by_module: dict[str, dict[str, dict]] = {}
        self.last_sync: dict | None = None

    def sync_module(self, module: str, desired: list) -> dict:
        existing = self.by_module.setdefault(module, {})
        desired_codes = {str(p["code"]): p for p in desired if p.get("code")}

        deleted = 0
        for code in list(existing.keys()):
            if code not in desired_codes:
                del existing[code]
                deleted += 1

        kept = 0
        inserted = 0
        for code, item in desired_codes.items():
            if code in existing:
                existing[code]["name"] = item.get("name")
                existing[code]["description"] = item.get("description")
                kept += 1
            else:
                existing[code] = {
                    "id": str(uuid4()),
                    "code": code,
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "module": module,
                }
                inserted += 1

        summary = {
            "kept": kept,
            "inserted": inserted,
            "deleted": deleted,
            "codes": sorted(desired_codes.keys()),
        }
        self.last_sync = summary
        return summary

    def bulk_create(self, permissions):
        raise AssertionError("bulk_create should not be used for plugin register sync")

    def delete_by_module(self, module: str):
        raise AssertionError("delete_by_module should not be used for plugin register sync")


class FakeUoW:
    def __init__(self, exists=False):
        self.plugins = FakePlugins(exists)
        self.plugin_manifests = SimpleNamespace(save=lambda *a, **k: None)
        self.plugin_versions = SimpleNamespace(
            create=lambda *a, **k: None,
            exists=lambda *a, **k: False,
        )
        self.plugin_permissions = FakePluginPermissions()
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

    result = use_case.execute({
        **base_manifest(),
        "icon": "layout-dashboard",
        "description": "desc",
    })

    assert result.success
    assert uow.plugins.created
    assert uow.plugins.last_create == {
        "id": "crm",
        "name": "CRM",
        "description": "desc",
        "base_path": "/apps/crm",
        "icon": "layout-dashboard",
        "type": "microfrontend",
        "version": "1.0.0",
        "active": True,
    }


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


def test_register_new_version_preserves_permission_ids_for_same_codes():
    uow = FakeUoW(exists=True)
    # seed previous version permissions
    uow.plugin_permissions.sync_module(
        "crm",
        [
            {"code": "crm.view", "name": "View", "description": None, "module": "crm"},
            {"code": "crm.edit", "name": "Edit", "description": None, "module": "crm"},
        ],
    )
    old_view_id = uow.plugin_permissions.by_module["crm"]["crm.view"]["id"]
    old_edit_id = uow.plugin_permissions.by_module["crm"]["crm.edit"]["id"]

    use_case = RegisterPluginUseCase(uow, FakeValidator(True))
    manifest = {
        **base_manifest(),
        "version": "1.0.1",
        "permissions": [
            {"code": "crm.view", "name": "View updated", "description": "x"},
            {"code": "crm.admin", "name": "Admin"},
        ],
        "routes": [
            {"path": "/apps/crm", "label": "CRM", "permission": "crm.view", "order": 10},
        ],
    }

    result = use_case.execute(manifest)

    assert result.success
    assert uow.plugin_routes.deleted_app == "crm"
    assert uow.plugin_permissions.by_module["crm"]["crm.view"]["id"] == old_view_id
    assert "crm.edit" not in uow.plugin_permissions.by_module["crm"]
    assert "crm.admin" in uow.plugin_permissions.by_module["crm"]
    assert uow.plugin_permissions.last_sync == {
        "kept": 1,
        "inserted": 1,
        "deleted": 1,
        "codes": ["crm.admin", "crm.view"],
    }
    # edit was deleted; view kept same id
    assert old_edit_id not in {
        p["id"] for p in uow.plugin_permissions.by_module["crm"].values()
    }


def test_register_new_version_syncs_app_icon_and_identity():
    """Gap: register só atualizava version — sidebar lia apps.icon antigo."""
    uow = FakeUoW(exists=True)
    use_case = RegisterPluginUseCase(uow, FakeValidator(True))

    manifest = {
        **base_manifest(),
        "version": "1.1.0",
        "name": "CRM Novo",
        "description": "Desc nova",
        "icon": "briefcase-business",
        "type": "microfrontend",
        "basePath": "/apps/crm",
        "routes": [
            {
                "path": "/apps/crm",
                "label": "CRM",
                "permission": "crm.view",
                "icon": "layout-dashboard",
                "order": 1,
            },
        ],
    }

    result = use_case.execute(manifest)

    assert result.success
    assert uow.plugins.last_update_version["version"] == "1.1.0"
    assert uow.plugins.last_update_metadata == {
        "plugin_id": "crm",
        "name": "CRM Novo",
        "description": "Desc nova",
        "icon": "briefcase-business",
        "app_type": "microfrontend",
        "base_path": "/apps/crm",
        "actor_user_id": None,
        "actor_name": None,
    }


def test_register_first_create_forces_module_plugin_id():
    uow = FakeUoW(exists=False)
    use_case = RegisterPluginUseCase(uow, FakeValidator(True))

    manifest = {
        **base_manifest(),
        "permissions": [
            {
                "code": "crm.view",
                "name": "View",
                "description": None,
                "module": "wrong-module",
            }
        ],
    }

    result = use_case.execute(manifest)

    assert result.success
    assert list(uow.plugin_permissions.by_module.keys()) == ["crm"]
    assert uow.plugin_permissions.by_module["crm"]["crm.view"]["module"] == "crm"
