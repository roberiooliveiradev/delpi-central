"""Seleção genérica tv_dashboard_copilot via suggest-ops (sem ops embutidas)."""

from __future__ import annotations

from app.application.services.chat_tv_dashboard_catalog_service import (
    ChatTvDashboardCatalogService,
)
from app.application.services.chat_tv_dashboard_platform_tool_selection_service import (
    ChatTvDashboardPlatformToolSelectionService,
)
from app.domain.ports.tv_dashboard_capability_catalog_port import (
    TvDashboardCapabilityCatalogPort,
)
from app.domain.services.chat_fast_path_service import ChatFastPathService
from app.domain.services.chat_host_surface_context_service import (
    ChatHostSurfaceContextService,
)
from app.domain.services.chat_tv_dashboard_copilot_intent_service import (
    ChatTvDashboardCopilotIntentService,
)
from app.domain.services.chat_advanced_sql_specialist_service import (
    ChatAdvancedSqlSpecialistService,
)


class _FakeCatalogPort(TvDashboardCapabilityCatalogPort):
    def __init__(
        self,
        *,
        catalog: dict | None = None,
        suggestion: dict | None = None,
        fail_catalog: bool = False,
        fail_suggest: bool = False,
    ) -> None:
        self.catalog = catalog
        self.suggestion = suggestion
        self.fail_catalog = fail_catalog
        self.fail_suggest = fail_suggest
        self.fetch_calls = 0
        self.suggest_calls = 0

    def fetch_catalog(self, access_token: str) -> dict | None:
        self.fetch_calls += 1
        if self.fail_catalog:
            return None
        return dict(self.catalog) if isinstance(self.catalog, dict) else None

    def suggest_ops(self, message: str, host_context: dict | None, access_token: str) -> dict | None:
        self.suggest_calls += 1
        if self.fail_suggest:
            return None
        return dict(self.suggestion) if isinstance(self.suggestion, dict) else None


_TV_WORKSPACE = {
    "skills": {"tvDashboardCopilot": True},
    "tvDashboardHostContext": {
        "surface": "tv-dashboard",
        "playlistId": "pl-live",
        "slideId": "sl-1",
    },
}


def test_suggest_ops_builds_tool_without_ai_knowing_op_name():
    port = _FakeCatalogPort(
        catalog={
            "catalogVersion": "test.1",
            "capabilities": [
                {
                    "op": "upsert_block",
                    "whenToUse": "Inserir texto no slide",
                }
            ],
        },
        suggestion={
            "catalogVersion": "test.1",
            "ops": [
                {
                    "op": "upsert_block",
                    "block": {"type": "text", "content": "Olá fábrica"},
                }
            ],
            "reason": "sugestão BFF",
        },
    )
    result = ChatTvDashboardPlatformToolSelectionService.select(
        'escreva um texto "Olá fábrica" neste slide',
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is not None
    assert result.tool_call["name"] == "tv_dashboard_copilot"
    assert result.tool_call["arguments"]["mode"] == "preview"
    assert result.tool_call["arguments"]["ops"][0]["op"] == "upsert_block"
    assert result.tool_call["arguments"]["target"]["playlistId"] == "pl-live"
    assert port.fetch_calls == 1
    assert port.suggest_calls == 1


def test_safe_plan_applies_directly_without_confirmation():
    port = _FakeCatalogPort(
        catalog={"catalogVersion": "test.direct", "capabilities": []},
        suggestion={
            "status": "ready",
            "catalogVersion": "test.direct",
            "ops": [{"op": "add_blank_slide", "title": "Produção"}],
            "confirmationPolicy": "direct",
            "risk": "additive",
            "reason": "Plano pronto — execução direta.",
        },
    )

    result = ChatTvDashboardPlatformToolSelectionService.select(
        "crie um slide",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )

    assert result.tool_call is not None
    assert result.tool_call["arguments"]["mode"] == "apply"
    assert result.tool_call["arguments"]["confirmationPolicy"] == "direct"
    assert result.tool_call["arguments"]["risk"] == "additive"


def test_destructive_plan_previews_and_waits_for_confirmation():
    port = _FakeCatalogPort(
        catalog={"catalogVersion": "test.confirm", "capabilities": []},
        suggestion={
            "status": "ready",
            "catalogVersion": "test.confirm",
            "ops": [{"op": "delete_block", "blockId": "blk-1"}],
            "confirmationPolicy": "confirm",
            "risk": "destructive",
            "reason": "Exclusão exige confirmação.",
        },
    )

    result = ChatTvDashboardPlatformToolSelectionService.select(
        "apague o bloco",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )

    assert result.tool_call is not None
    assert result.tool_call["arguments"]["mode"] == "preview"
    assert result.tool_call["arguments"]["confirmationPolicy"] == "confirm"
    assert result.tool_call["arguments"]["risk"] == "destructive"


def test_confirmation_guard_uses_bff_policy_not_all_apply_calls():
    assert (
        ChatTvDashboardCopilotIntentService.requires_confirmation(
            {"mode": "apply", "confirmationPolicy": "direct"}
        )
        is False
    )
    assert (
        ChatTvDashboardCopilotIntentService.requires_confirmation(
            {"mode": "apply", "confirmationPolicy": "confirm"}
        )
        is True
    )
    assert (
        ChatTvDashboardCopilotIntentService.requires_confirmation({"mode": "apply"})
        is True
    )


def test_catalog_failure_returns_no_tool_and_unavailable_answer():
    port = _FakeCatalogPort(fail_catalog=True)
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "crie um slide",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is None
    assert result.direct_answer
    assert "catálogo" in result.direct_answer.lower() or "catalogo" in (
        result.direct_answer.lower()
    )


def test_empty_suggest_ops_returns_bff_reason_as_direct_answer():
    """Match incompleto no BFF → directAnswer com reason; sem tool / sem LLM inventar UI."""
    port = _FakeCatalogPort(
        catalog={"catalogVersion": "test.1", "capabilities": []},
        suggestion={
            "catalogVersion": "test.1",
            "ops": [],
            "matchedCapabilityKeys": ["patch_native_config"],
            "clarificationKey": "suggestNeedColor",
            "reason": "Indique a cor do fundo (ex.: azul, #2563eb).",
        },
    )
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "mude a cor do fundo do slide",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is None
    assert result.has_suggested_ops is False
    assert result.direct_answer == (
        "Indique a cor do fundo (ex.: azul, #2563eb)."
    )
    assert result.catalog is not None


def test_planner_not_command_leaves_turn_for_normal_pipeline():
    """Pergunta na superfície TV: o planner diz que não é comando de editor."""
    port = _FakeCatalogPort(
        catalog={"catalogVersion": "test.nc", "capabilities": []},
        suggestion={
            "status": "not_command",
            "catalogVersion": "test.nc",
            "ops": [],
            "reason": "",
        },
    )
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "quem é você",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is None
    assert result.direct_answer is None
    assert result.catalog is not None


def test_planner_unsupported_answers_catalog_capabilities():
    port = _FakeCatalogPort(
        catalog={"catalogVersion": "test.uns", "capabilities": []},
        suggestion={
            "status": "unsupported",
            "catalogVersion": "test.uns",
            "ops": [],
            "reason": "Não identifiquei uma operação do catálogo. Exemplos: «crie um slide».",
        },
    )
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "exporte o slide para powerpoint",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is None
    assert result.direct_answer
    assert "crie um slide" in result.direct_answer


def test_typo_reaches_bff_because_ai_does_not_gate_by_local_vocabulary():
    """«crie um sldie» não casa no vocabulário local — o planner decide."""
    port = _FakeCatalogPort(
        catalog={"catalogVersion": "test.typo", "capabilities": []},
        suggestion={
            "status": "ready",
            "catalogVersion": "test.typo",
            "ops": [{"op": "add_blank_slide", "title": "Slide personalizado"}],
            "confirmationPolicy": "direct",
            "risk": "additive",
            "reason": "Plano pronto.",
        },
    )
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "crie um sldie",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert port.suggest_calls == 1
    assert result.tool_call is not None
    assert result.tool_call["arguments"]["mode"] == "apply"


def test_bff_offline_does_not_hijack_small_talk():
    port = _FakeCatalogPort(fail_catalog=True)
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "obrigado",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is None
    assert result.direct_answer is None


def test_suggest_failure_returns_unavailable_answer():
    port = _FakeCatalogPort(
        catalog={"catalogVersion": "test.1", "capabilities": []},
        fail_suggest=True,
    )
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "crie um slide",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is None
    assert result.direct_answer
    assert result.catalog is not None


def test_fake_capability_only_in_bff_flows_to_tool():
    """AP: op nova só no BFF — AI não precisa conhecer o nome no matching."""
    port = _FakeCatalogPort(
        catalog={
            "catalogVersion": "test.fake",
            "capabilities": [
                {"op": "paint_slide_neon", "whenToUse": "Pintar slide de neon"}
            ],
        },
        suggestion={
            "catalogVersion": "test.fake",
            "ops": [{"op": "paint_slide_neon", "color": "#0ff"}],
            "matchedCapabilityKeys": ["paint_slide_neon"],
        },
    )
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "crie um slide neon",
        workspace_context=_TV_WORKSPACE,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call["arguments"]["ops"][0]["op"] == "paint_slide_neon"


def test_apply_confirmation_from_history_skips_suggest():
    port = _FakeCatalogPort(fail_catalog=True)
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
                            "ops": [{"op": "add_blank_slide", "title": "X"}],
                            "target": {"playlistId": "pl-1"},
                        },
                        "metadata": {"ok": True, "mode": "preview"},
                    }
                ]
            },
        }
    ]
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "pode aplicar",
        workspace_context=_TV_WORKSPACE,
        previous_messages=previous,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is not None
    assert result.tool_call["arguments"]["mode"] == "apply"
    assert result.tool_call["arguments"]["ops"][0]["op"] == "add_blank_slide"
    assert port.fetch_calls == 0


def _tv_history(call_metadata: dict, *, arguments: dict | None = None) -> list[dict]:
    return [
        {
            "role": "assistant",
            "content": "prévia",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "tv_dashboard_copilot",
                        "arguments": arguments
                        if arguments is not None
                        else {
                            "mode": "preview",
                            "ops": [{"op": "add_blank_slide", "title": "X"}],
                            "target": {"playlistId": "pl-1"},
                        },
                        "metadata": call_metadata,
                    }
                ]
            },
        }
    ]


def test_confirmation_after_failed_preview_answers_no_pending_patch():
    """Preview que falhou no BFF não vira apply nem cai no LLM."""
    port = _FakeCatalogPort(fail_catalog=True)
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "confirmo",
        workspace_context=_TV_WORKSPACE,
        previous_messages=_tv_history({"ok": False, "mode": "preview"}),
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is None
    assert result.direct_answer == (
        ChatTvDashboardCopilotIntentService.no_pending_preview_message()
    )
    assert port.fetch_calls == 0


def test_confirmation_after_apply_does_not_reapply_older_preview():
    port = _FakeCatalogPort(fail_catalog=True)
    previous = _tv_history({"ok": True, "mode": "preview"}) + _tv_history(
        {"ok": True, "mode": "apply"},
        arguments={
            "mode": "apply",
            "ops": [{"op": "add_blank_slide", "title": "X"}],
            "target": {"playlistId": "pl-1"},
        },
    )
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "confirmo",
        workspace_context=_TV_WORKSPACE,
        previous_messages=previous,
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is None
    assert result.direct_answer == (
        ChatTvDashboardCopilotIntentService.no_pending_preview_message()
    )


def test_confirmation_without_tv_history_does_not_hijack_turn():
    port = _FakeCatalogPort(fail_catalog=True)
    result = ChatTvDashboardPlatformToolSelectionService.select(
        "confirmo",
        workspace_context=_TV_WORKSPACE,
        previous_messages=[],
        access_token="tok",
        catalog_service=ChatTvDashboardCatalogService(catalog_port=port),
    )
    assert result.tool_call is None
    assert result.direct_answer is None


def test_failed_preview_direct_answer_reports_failure():
    answer = ChatTvDashboardCopilotIntentService.format_direct_answer(
        data={},
        metadata={"ok": False, "mode": "preview", "httpStatus": 502},
    )
    assert answer
    assert "prévia" in answer.lower()
    assert "confirmo" not in answer.lower()


def test_failed_apply_preserves_factual_bff_reason():
    answer = ChatTvDashboardCopilotIntentService.format_direct_answer(
        data={"message": "O slide foi alterado por outro editor."},
        metadata={"ok": False, "mode": "apply", "httpStatus": 409},
    )
    assert answer == "O slide foi alterado por outro editor."


def test_is_tv_mutation_turn_and_anti_hijack():
    host = {"surface": "tv-dashboard", "playlistId": "pl-1", "slideId": "sl-1"}
    assert (
        ChatHostSurfaceContextService.is_tv_mutation_turn(
            "crie um slide",
            host,
        )
        is True
    )
    assert ChatFastPathService.should_use(
        "crie um slide",
        host_context=host,
        workspace_context={"tvDashboardHostContext": host},
    ) is False

    sql_ctx = {
        "skills": {"sqlAuthoring": True, "tvDashboardCopilot": True},
        "tvDashboardHostContext": host,
    }
    assert (
        ChatAdvancedSqlSpecialistService.should_activate(
            "crie um slide",
            workspace_context=sql_ctx,
        )
        is False
    )


def test_prompt_addon_includes_catalog_when_to_use():
    addon = ChatHostSurfaceContextService.build_prompt_addon(
        {
            "skills": {"tvDashboardCopilot": True},
            "tvDashboardHostContext": {
                "surface": "tv-dashboard",
                "playlistId": "pl-42",
            },
        },
        catalog={
            "catalogVersion": "1",
            "capabilities": [
                {"op": "upsert_block", "whenToUse": "Inserir bloco de texto no slide"}
            ],
        },
    )
    assert "pl-42" in addon
    assert "Inserir bloco de texto" in addon
