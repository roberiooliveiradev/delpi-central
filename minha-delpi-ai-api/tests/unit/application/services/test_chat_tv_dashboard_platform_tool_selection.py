"""Handoff TV Dashboard → VISTA (sem tool de mutação)."""

from __future__ import annotations

from app.application.services.chat_tv_dashboard_platform_tool_selection_service import (
    ChatTvDashboardPlatformToolSelectionService,
)
from app.domain.services.chat_tv_dashboard_handoff_service import (
    ChatTvDashboardHandoffService,
)

_TV_WORKSPACE = {
    "skills": {},
    "hostContext": {"surface": "tv-dashboard", "playlistId": "pl-1", "slideId": "sl-1"},
}


def test_tv_phrase_returns_vista_handoff_without_tool():
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "crie um slide de OEE",
        workspace_context=_TV_WORKSPACE,
    )
    assert result.tool_call is None
    assert result.platform_direct_answer is True
    assert result.direct_answer == ChatTvDashboardHandoffService.redirect_to_vista_message()
    assert "VISTA" in (result.direct_answer or "")


def test_non_tv_message_returns_empty():
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "qual o horário do refeitório?",
        workspace_context={"skills": {}},
    )
    assert result.tool_call is None
    assert result.direct_answer is None
    assert result.platform_direct_answer is False


def test_enrich_workspace_clears_legacy_skill_flag():
    workspace = ChatTvDashboardHandoffService.enrich_workspace(
        {"skills": {"tvDashboardCopilot": True}},
        message="crie um slide",
        host_context={"surface": "tv-dashboard", "playlistId": "p1"},
    )
    assert workspace["skills"].get("tvDashboardCopilot") is None
    assert workspace["tvDashboardHostContext"]["playlistId"] == "p1"
