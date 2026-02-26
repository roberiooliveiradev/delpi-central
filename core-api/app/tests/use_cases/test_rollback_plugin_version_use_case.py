# app/tests/use_cases/test_rollback_plugin_version_use_case.py

from app.application.use_cases.rollback_plugin_version_use_case import RollbackPluginVersionUseCase


class FakeUoW:
    def __init__(self, plugin=True, version=True):
        self.plugins = type("", (), {
            "get_by_id": lambda s, pid: {"id": pid} if plugin else None,
            "update_version": lambda *a, **k: None,
        })()

        self.plugin_versions = type("", (), {
            "get_version": lambda s, pid, v: {"manifest": {"routes": [], "permissions": []}, "checksum": "abc"} if version else None,
        })()

        self.plugin_manifests = type("", (), {"save": lambda *a, **k: None})()
        self.plugin_routes = type("", (), {
            "delete_by_app": lambda *a, **k: None,
            "bulk_create": lambda *a, **k: None,
        })()
        self.plugin_permissions = type("", (), {
            "delete_by_module": lambda *a, **k: None,
            "bulk_create": lambda *a, **k: None,
        })()

        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_rollback_success():
    uow = FakeUoW(plugin=True, version=True)
    use_case = RollbackPluginVersionUseCase(uow)

    result = use_case.execute("crm", "1.0.0")

    assert result.success
    assert uow.committed


def test_rollback_plugin_not_found():
    uow = FakeUoW(plugin=False)
    use_case = RollbackPluginVersionUseCase(uow)

    result = use_case.execute("crm", "1.0.0")

    assert not result.success
    assert result.errors[0]["code"] == "plugin.not_found"