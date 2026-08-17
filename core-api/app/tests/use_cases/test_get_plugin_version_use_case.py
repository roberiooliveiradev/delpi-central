# app/tests/use_cases/test_get_plugin_version_use_case.py

from app.application.use_cases.get_plugin_version_use_case import GetPluginVersionUseCase


class FakeUoW:
    def __init__(self, plugin=True, version=True):
        self.plugins = type(
            "",
            (),
            {"get_by_id": lambda s, pid: {"id": pid} if plugin else None},
        )()
        self.plugin_versions = type(
            "",
            (),
            {
                "get_version": lambda s, pid, v: (
                    {
                        "version": v,
                        "checksum": "abc",
                        "created_at": "2026-01-01T00:00:00",
                        "manifest": {"id": pid, "version": v},
                    }
                    if version
                    else None
                )
            },
        )()


def test_get_version_success():
    result = GetPluginVersionUseCase(FakeUoW()).execute("crm", "1.0.0")
    assert result.success
    assert result.version["manifest"]["id"] == "crm"
    assert result.version["version"] == "1.0.0"


def test_get_version_plugin_not_found():
    result = GetPluginVersionUseCase(FakeUoW(plugin=False)).execute("crm", "1.0.0")
    assert not result.success
    assert result.errors[0]["code"] == "plugin.not_found"


def test_get_version_not_found():
    result = GetPluginVersionUseCase(FakeUoW(version=False)).execute("crm", "9.9.9")
    assert not result.success
    assert result.errors[0]["code"] == "plugin.version_not_found"
