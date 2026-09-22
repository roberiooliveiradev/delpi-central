"""Handoff TV Dashboard → VISTA (sem tool de mutação)."""

from __future__ import annotations

from app.application.services.chat_tv_dashboard_platform_tool_selection_service import (
    ChatTvDashboardPlatformToolSelectionService,
)
from app.domain.services.chat_tv_dashboard_copilot_intent_service import (
    ChatTvDashboardCopilotIntentService,
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
    assert result.direct_answer == ChatTvDashboardCopilotIntentService.redirect_to_vista_message()
    assert "VISTA" in (result.direct_answer or "")


def test_non_tv_message_returns_empty():
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "qual o horário do refeitório?",
        workspace_context={"skills": {}},
    )
    assert result.tool_call is None
    assert result.direct_answer is None
    assert result.platform_direct_answer is False


def test_should_enable_skill_always_false():
    assert (
        ChatTvDashboardCopilotIntentService.should_enable_skill(
            "crie um slide",
            host_context={"surface": "tv-dashboard"},
            already_enabled=True,
        )
        is False
    )


def test_build_apply_from_history_always_none():
    previous = [
        {
            "role": "assistant",
            "toolCalls": [
                {
                    "name": "tv_dashboard_copilot",
                    "arguments": {
                        "mode": "preview",
                        "ops": [{"op": "addSlide"}],
                        "confirmationPolicy": "confirm",
                    },
                    "metadata": {"ok": True},
                }
            ],
        }
    ]
    assert (
        ChatTvDashboardCopilotIntentService.build_apply_tool_call_from_history(previous)
        is None
    )


def test_enrich_workspace_clears_skill_flag():
    workspace = ChatTvDashboardCopilotIntentService.enrich_workspace_skills(
        {"skills": {"tvDashboardCopilot": True}},
        message="crie um slide",
        host_context={"surface": "tv-dashboard", "playlistId": "p1"},
    )
    assert workspace["skills"].get("tvDashboardCopilot") is None
    assert workspace["tvDashboardHostContext"]["playlistId"] == "p1"
