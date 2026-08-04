"""Contexto ambient de host + exclusão de text_task no surface TV."""

from app.application.services.chat_tv_dashboard_catalog_service import (
    ChatTvDashboardCatalogService,
)
from app.application.services.chat_tv_dashboard_platform_tool_selection_service import (
    ChatTvDashboardPlatformToolSelectionService,
)
from app.domain.ports.tv_dashboard_capability_catalog_port import (
    TvDashboardCapabilityCatalogPort,
)
from app.domain.services.chat_host_surface_context_service import (
    ChatHostSurfaceContextService,
)
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
from app.domain.services.chat_tv_dashboard_copilot_intent_service import (
    ChatTvDashboardCopilotIntentService,
)


class _SuggestSlidePort(TvDashboardCapabilityCatalogPort):
    def fetch_catalog(self, access_token: str) -> dict | None:
        return {
            "catalogVersion": "t",
            "capabilities": [{"op": "add_slide_from_preset", "whenToUse": "Slide"}],
        }

    def suggest_ops(self, message, host_context, access_token):
        return {
            "catalogVersion": "t",
            "ops": [{"op": "add_slide_from_preset", "presetKey": "preset_comunicado"}],
            "reason": "BFF",
        }


def test_matches_create_slide_without_host():
    assert ChatTvDashboardCopilotIntentService.matches("crie um slide") is True
    assert ChatTextTaskIntentService.is_pure_text_task("crie um slide") is False


def test_normalize_host_context_preserves_operation_and_data_source_ids():
    normalized = ChatTvDashboardCopilotIntentService.normalize_host_context(
        {
            "surface": "tv-dashboard",
            "playlistId": "pl-1",
            "slideId": "sl-1",
            "operationId": "get_overall_equipment_effectiveness_pct",
            "dataSourceId": "ds-9",
            "selectedDataSourceId": "ds-9",
            "selectedVisualId": "viz-1",
            "presetKey": "production_oee_overview",
            "selectedBlockIds": ["viz-1"],
            "dataSources": [
                {
                    "id": "ds-9",
                    "operationId": "get_overall_equipment_effectiveness_pct",
                    "label": "OEE",
                }
            ],
        }
    )
    assert normalized is not None
    assert normalized["operationId"] == "get_overall_equipment_effectiveness_pct"
    assert normalized["dataSourceId"] == "ds-9"
    assert normalized["selectedDataSourceId"] == "ds-9"
    assert normalized["selectedVisualId"] == "viz-1"
    assert normalized["presetKey"] == "production_oee_overview"
    assert normalized["selectedBlockIds"] == ["viz-1"]
    assert normalized["dataSources"][0]["label"] == "OEE"


def test_surface_tv_enables_skill_without_message_keywords():
    host = {"surface": "tv-dashboard", "playlistId": "pl-1"}
    workspace = ChatHostSurfaceContextService.enrich_workspace(
        {"skills": {}},
        message="olá",
        host_context=host,
    )
    assert workspace["skills"]["tvDashboardCopilot"] is True
    assert workspace["tvDashboardHostContext"]["playlistId"] == "pl-1"


def test_surface_tv_write_imperative_is_not_pure_text_task():
    host = {"surface": "tv-dashboard", "playlistId": "pl-1"}
    assert (
        ChatTextTaskIntentService.is_pure_text_task(
            "crie um slide",
            host_context=host,
        )
        is False
    )
    assert (
        ChatTextTaskIntentService.is_pure_text_task(
            "monte algo simples",
            host_context=host,
        )
        is False
    )


def test_surface_tv_keeps_email_as_text_task():
    host = {"surface": "tv-dashboard", "playlistId": "pl-1"}
    assert (
        ChatTextTaskIntentService.is_pure_text_task(
            "escreva um e-mail cobrando o fornecedor",
            host_context=host,
        )
        is True
    )


def test_merge_tool_target_from_host():
    workspace = {
        "tvDashboardHostContext": {
            "surface": "tv-dashboard",
            "playlistId": "pl-99",
            "slideId": "sl-1",
        }
    }
    args = ChatHostSurfaceContextService.merge_tool_arguments(
        "tv_dashboard_copilot",
        {"mode": "preview", "ops": [{"op": "add_slide_from_preset", "presetKey": "preset_comunicado"}]},
        workspace,
    )
    assert args["target"]["playlistId"] == "pl-99"
    assert args["target"]["slideId"] == "sl-1"


def test_host_prompt_addon_includes_playlist():
    addon = ChatHostSurfaceContextService.build_prompt_addon(
        {
            "skills": {"tvDashboardCopilot": True},
            "tvDashboardHostContext": {
                "surface": "tv-dashboard",
                "playlistId": "pl-42",
            },
        }
    )
    assert "pl-42" in addon
    assert "tv-dashboard" in addon or "surface" in addon.lower()


def test_allows_common_chat_platform_tools_when_skill_or_surface():
    assert (
        ChatHostSurfaceContextService.allows_common_chat_platform_tools(
            {"skills": {"tvDashboardCopilot": True}},
            message="olá",
        )
        is True
    )
    assert (
        ChatHostSurfaceContextService.allows_common_chat_platform_tools(
            {"tvDashboardHostContext": {"surface": "tv-dashboard"}},
            message="olá",
        )
        is True
    )
    assert (
        ChatHostSurfaceContextService.allows_common_chat_platform_tools(
            {"skills": {}},
            message="crie um slide",
        )
        is True
    )
    assert (
        ChatHostSurfaceContextService.allows_common_chat_platform_tools(
            {"skills": {}},
            message="olá",
        )
        is False
    )


def test_platform_tool_selection_create_slide_merges_playlist():
    call = ChatTvDashboardPlatformToolSelectionService.select(
        "crie um slide",
        workspace_context={
            "skills": {"tvDashboardCopilot": True},
            "tvDashboardHostContext": {
                "surface": "tv-dashboard",
                "playlistId": "pl-live",
            },
        },
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=_SuggestSlidePort()),
    ).tool_call
    assert call is not None
    assert call["name"] == "tv_dashboard_copilot"
    assert call["arguments"]["mode"] == "preview"
    assert call["arguments"]["ops"][0]["op"] == "add_slide_from_preset"
    assert call["arguments"]["target"]["playlistId"] == "pl-live"


def test_build_platform_tool_call_skips_non_slide_message():
    assert (
        ChatHostSurfaceContextService.build_platform_tool_call(
            "olá",
            workspace_context={
                "skills": {"tvDashboardCopilot": True},
                "tvDashboardHostContext": {"surface": "tv-dashboard"},
            },
        )
        is None
    )
    assert (
        ChatTvDashboardPlatformToolSelectionService.select(
            "olá",
            workspace_context={
                "skills": {"tvDashboardCopilot": True},
                "tvDashboardHostContext": {"surface": "tv-dashboard"},
            },
            access_token="tok",
            catalog_service=ChatTvDashboardCatalogService(catalog_port=_SuggestSlidePort()),
        ).tool_call
        is None
    )


def test_build_platform_tool_call_apply_after_preview_confirmation():
    previous = [
        {
            "role": "assistant",
            "content": "prévia",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "tv_dashboard_copilot",
                        "arguments": {
                            "mode": "preview",
                            "ops": [
                                {
                                    "op": "add_slide_from_preset",
                                    "presetKey": "preset_comunicado",
                                }
                            ],
                            "target": {"playlistId": "pl-1"},
                        },
                        "metadata": {"ok": True, "mode": "preview"},
                    }
                ]
            },
        }
    ]
    call = ChatHostSurfaceContextService.build_platform_tool_call(
        "pode aplicar",
        workspace_context={
            "skills": {"tvDashboardCopilot": True},
            "tvDashboardHostContext": {
                "surface": "tv-dashboard",
                "playlistId": "pl-1",
            },
        },
        previous_messages=previous,
    )
    assert call is not None
    assert call["arguments"]["mode"] == "apply"
    assert call["arguments"]["ops"][0]["op"] == "add_slide_from_preset"
    assert call["arguments"]["target"]["playlistId"] == "pl-1"


def test_build_apply_from_chat_message_entity():
    from types import SimpleNamespace

    previous = [
        SimpleNamespace(
            role="assistant",
            content="prévia",
            metadata={
                "toolCalls": [
                    {
                        "name": "tv_dashboard_copilot",
                        "arguments": {
                            "mode": "preview",
                            "ops": [{"op": "add_slide_from_preset", "presetKey": "preset_comunicado"}],
                            "target": {"playlistId": "pl-9"},
                        },
                        "metadata": {"ok": True, "mode": "preview"},
                    }
                ]
            },
        )
    ]
    call = ChatTvDashboardCopilotIntentService.build_apply_tool_call_from_history(previous)
    assert call is not None
    assert call["arguments"]["mode"] == "apply"
    assert call["arguments"]["target"]["playlistId"] == "pl-9"
