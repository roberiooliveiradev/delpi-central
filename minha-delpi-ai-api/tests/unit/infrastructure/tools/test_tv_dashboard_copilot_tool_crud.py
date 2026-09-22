"""Stub gone — apply via CRUD não é mais caminho Chat."""

from app.infrastructure.tools.tv_dashboard_copilot_tool import TvDashboardCopilotTool


def test_tv_copilot_apply_mode_also_returns_gone():
    tool = TvDashboardCopilotTool()
    result = tool.execute(
        {
            "mode": "apply",
            "target": {"playlistId": "p", "slideId": "s"},
            "ops": [{"op": "upsert_block", "block": {"id": "b1"}}],
        },
        access_token="tok",
    )
    assert result.data.get("gone") is True
    assert result.metadata.get("ok") is False
    assert result.metadata.get("httpStatus") == 410
