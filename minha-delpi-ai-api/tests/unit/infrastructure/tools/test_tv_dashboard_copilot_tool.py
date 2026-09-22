"""Testes unitários do stub deprecated tv_dashboard_copilot."""

from app.infrastructure.tools.tv_dashboard_copilot_tool import TvDashboardCopilotTool


def test_tv_copilot_tool_refuses_with_gone():
    tool = TvDashboardCopilotTool()
    result = tool.execute(
        {
            "mode": "preview",
            "target": {"playlistId": "p", "slideId": "s"},
            "ops": [{"op": "upsert_block", "block": {"id": "b1"}}],
        },
        access_token="tok",
    )
    assert result.name == "tv_dashboard_copilot"
    assert result.data.get("gone") is True
    assert result.metadata.get("httpStatus") == 410
    assert "VISTA" in str(result.data.get("message") or "")


def test_tv_copilot_tool_name_stable():
    assert TvDashboardCopilotTool().name == "tv_dashboard_copilot"
