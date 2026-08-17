# app/tests/use_cases/test_rollback_plugin_version_use_case.py

from uuid import uuid4

from app.application.use_cases.rollback_plugin_version_use_case import (
    RollbackPluginVersionUseCase,
)


class FakePluginPermissions:
    def __init__(self):
        self.by_module: dict[str, dict[str, dict]] = {}
        self.last_sync = None

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
                kept += 1
            else:
                existing[code] = {
                    "id": str(uuid4()),
                    "code": code,
                    "name": item.get("name"),
                    "module": module,
                }
                inserted += 1

        self.last_sync = {
            "kept": kept,
            "inserted": inserted,
            "deleted": deleted,
            "codes": sorted(desired_codes.keys()),
        }
        return self.last_sync


class FakeUoW:
    def __init__(self, plugin=True, version=True, manifest=None):
        self.plugins = type(
            "",
            (),
            {
                "get_by_id": lambda s, pid: {"id": pid} if plugin else None,
                "update_version": lambda *a, **k: None,
            },
        )()

        stored = {
            "manifest": manifest
            if manifest is not None
            else {"routes": [], "permissions": []},
            "checksum": "abc",
        }

        self.plugin_versions = type(
            "",
            (),
            {
                "get_version": lambda s, pid, v: stored if version else None,
            },
        )()

        self.plugin_manifests = type("", (), {"save": lambda *a, **k: None})()
        self.plugin_routes = type(
            "",
            (),
            {
                "delete_by_app": lambda *a, **k: None,
                "bulk_create": lambda *a, **k: None,
            },
        )()
        self.plugin_permissions = FakePluginPermissions()
        self.events: list = []

    def collect_event(self, event):
        self.events.append(event)


def test_rollback_success():
    uow = FakeUoW(plugin=True, version=True)
    use_case = RollbackPluginVersionUseCase(uow)

    result = use_case.execute("crm", "1.0.0")

    assert result.success
    assert uow.plugin_permissions.last_sync is not None
    assert len(uow.events) == 1


def test_rollback_plugin_not_found():
    uow = FakeUoW(plugin=False)
    use_case = RollbackPluginVersionUseCase(uow)

    result = use_case.execute("crm", "1.0.0")

    assert not result.success
    assert result.errors[0]["code"] == "plugin.not_found"


def test_rollback_preserves_permission_ids_for_same_codes():
    uow = FakeUoW(
        plugin=True,
        version=True,
        manifest={
            "permissions": [
                {"code": "crm.view", "name": "View"},
            ],
            "routes": [],
        },
    )
    uow.plugin_permissions.sync_module(
        "crm",
        [
            {"code": "crm.view", "name": "Old", "module": "crm"},
            {"code": "crm.legacy", "name": "Legacy", "module": "crm"},
        ],
    )
    old_id = uow.plugin_permissions.by_module["crm"]["crm.view"]["id"]

    use_case = RollbackPluginVersionUseCase(uow)
    result = use_case.execute("crm", "1.0.0")

    assert result.success
    assert uow.plugin_permissions.by_module["crm"]["crm.view"]["id"] == old_id
    assert "crm.legacy" not in uow.plugin_permissions.by_module["crm"]
    assert uow.plugin_permissions.last_sync["deleted"] == 1
    assert uow.plugin_permissions.last_sync["kept"] == 1
