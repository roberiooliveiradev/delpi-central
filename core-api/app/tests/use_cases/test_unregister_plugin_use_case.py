# app/tests/use_cases/test_unregister_plugin_use_case.py

from app.application.use_cases.unregister_plugin_use_case import UnregisterPluginUseCase


class FakeUoW:
    def __init__(self, plugin_exists=True):
        self.plugins = type("", (), {
            "get_by_id": lambda s, pid: {"id": pid} if plugin_exists else None,
            "delete": lambda *a, **k: None,
        })()

        self.plugin_versions = type("", (), {"delete_by_app": lambda *a, **k: None})()
        self.plugin_routes = type("", (), {"delete_by_app": lambda *a, **k: None})()
        self.plugin_permissions = type("", (), {"delete_by_module": lambda *a, **k: None})()
        self.plugin_manifests = type("", (), {
            "delete": lambda *a, **k: None,
            "list_all": lambda s: [],
        })()

        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_unregister_success():
    uow = FakeUoW(plugin_exists=True)
    use_case = UnregisterPluginUseCase(uow)

    result = use_case.execute("crm")

    assert result.success
    assert uow.committed


def test_unregister_not_found():
    uow = FakeUoW(plugin_exists=False)
    use_case = UnregisterPluginUseCase(uow)

    result = use_case.execute("crm")

    assert not result.success
    assert result.errors[0]["code"] == "plugin.not_found"