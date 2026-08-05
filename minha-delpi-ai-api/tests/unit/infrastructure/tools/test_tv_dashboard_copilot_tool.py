"""Testes unitários do tool tv_dashboard_copilot."""

from app.infrastructure.tools.tv_dashboard_copilot_tool import TvDashboardCopilotTool


class _FakeGateway:
    def __init__(self):
        self.calls = []

    def preview_patch(self, envelope, *, access_token, include_fingerprint=True):
        self.calls.append(("preview", envelope, access_token, include_fingerprint))
        return {
            "_ok": True,
            "_httpStatus": 200,
            "ok": True,
            "data": {
                "ok": True,
                "appliedOps": ["upsert_data_source"],
                "persisted": False,
                "executionMode": "crud_http",
                "baseRevision": 1,
                "httpCommands": [
                    {
                        "method": "PATCH",
                        "path": "/playlists/p/slides/s",
                        "body": {"nativeConfig": {"blocks": []}},
                        "op": "native_config_batch",
                        "requiresIfMatch": True,
                        "expectedRevision": 1,
                    }
                ],
                "nativeConfig": {"blocks": []},
            },
        }

    def apply_patch(self, envelope, *, access_token):
        raise AssertionError("apply_patch must not be used for persistence")

    def execute_crud_command(self, command, *, access_token, expected_revision=None):
        self.calls.append(("crud", command, access_token, expected_revision))
        return {
            "_ok": True,
            "_httpStatus": 200,
            "ok": True,
            "data": {"id": "s"},
            "playlistRevision": (expected_revision or 1) + 1,
        }


def test_tv_copilot_tool_preview():
    gateway = _FakeGateway()
    tool = TvDashboardCopilotTool(gateway=gateway)
    result = tool.execute(
        {
            "mode": "preview",
            "target": {"playlistId": "p", "slideId": "s"},
            "ops": [{"op": "upsert_data_source", "operationId": "x"}],
        },
        access_token="tok",
    )
    assert result.name == "tv_dashboard_copilot"
    assert result.metadata["mode"] == "preview"
    assert result.metadata["sensitivity"] == "read"
    assert gateway.calls[0][0] == "preview"
    assert isinstance(result.data.get("httpCommands"), list)


def test_tv_copilot_tool_apply():
    gateway = _FakeGateway()
    tool = TvDashboardCopilotTool(gateway=gateway)
    result = tool.execute(
        {
            "mode": "apply",
            "target": {"playlistId": "p", "slideId": "s"},
            "ops": [{"op": "bind_visual", "visualId": "a", "dataSourceId": "b"}],
        },
        access_token="tok",
    )
    assert result.metadata["mode"] == "apply"
    assert result.metadata["sensitivity"] == "write"
    assert result.metadata["path"] == "/playlists (crud)"
    assert result.data.get("persisted") is True
    assert any(call[0] == "crud" for call in gateway.calls)
    assert not any(call[0] == "apply" for call in gateway.calls)


def test_tv_copilot_tool_description_uses_direct_policy():
    description = TvDashboardCopilotTool(gateway=_FakeGateway()).description

    assert "direct" in description
    assert "confirmationPolicy" in description
