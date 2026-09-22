"""Host surface TV — detecção e handoff (sem tool tv_dashboard_copilot)."""

from __future__ import annotations

from app.application.services.chat_tv_dashboard_platform_tool_selection_service import (
    ChatTvDashboardPlatformToolSelectionService,
)
from app.domain.services.chat_host_surface_context_service import (
    ChatHostSurfaceContextService,
)
from app.domain.services.chat_tv_dashboard_copilot_intent_service import (
    ChatTvDashboardCopilotIntentService,
)


def test_matches_explicit_tv_phrases():
    assert ChatTvDashboardCopilotIntentService.matches("crie um slide") is True
    assert ChatTvDashboardCopilotIntentService.matches_explicit_phrase("monte um slide") is True


def test_normalize_host_context():
    normalized = ChatTvDashboardCopilotIntentService.normalize_host_context(
        {"surface": "tv-dashboard", "playlistId": "pl-1", "slideId": "sl-1"}
    )
    assert normalized["surface"] == "tv-dashboard"
    assert normalized["playlistId"] == "pl-1"


def test_enrich_workspace_does_not_enable_skill():
    workspace = ChatHostSurfaceContextService.enrich_workspace(
        {"skills": {}},
        message="crie um slide",
        host_context={"surface": "tv-dashboard", "playlistId": "pl-1"},
    )
    assert "tvDashboardCopilot" not in workspace.get("skills", {})
    assert workspace["tvDashboardHostContext"]["playlistId"] == "pl-1"


def test_allows_common_chat_platform_tools_on_tv_phrase():
    assert ChatHostSurfaceContextService.allows_common_chat_platform_tools(
        {"skills": {}},
        message="crie um slide",
    )


def test_platform_selection_is_handoff_only():
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "crie um slide",
        workspace_context={
            "skills": {},
            "hostContext": {"surface": "tv-dashboard"},
        },
    )
    assert result.tool_call is None
    assert result.platform_direct_answer is True
    assert "VISTA" in (result.direct_answer or "")


def test_build_platform_tool_call_always_none():
    assert (
        ChatHostSurfaceContextService.build_platform_tool_call(
            "sim, aplica",
            workspace_context={
                "skills": {},
                "hostContext": {"surface": "tv-dashboard"},
            },
            previous_messages=[
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
            ],
        )
        is None
    )


def test_suppresses_pure_text_task_for_tv_create():
    assert ChatHostSurfaceContextService.suppresses_pure_text_task(
        "crie um slide",
        host_context={"surface": "tv-dashboard"},
        category="write",
    )
