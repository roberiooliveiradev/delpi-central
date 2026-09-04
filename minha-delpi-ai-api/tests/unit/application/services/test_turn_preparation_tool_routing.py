from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
    ChatTurnPreparationToolRoutingService,
)


@pytest.fixture(autouse=True)
def _patch_intelligence_runtime(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_intelligence_runtime_access.resolve_chat_intelligence_runtime",
        lambda: SimpleNamespace(assistant_identity_direct_enabled=True),
    )


def test_resolve_skip_tool_flags_for_assistant_identity_question():
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="quem é vc?",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[],
    )

    assert flags.skip_tools_for_assistant_identity is True
    assert flags.skip_tools_for_user_identity is False


def test_yoy_revise_does_not_skip_tools_for_data_interpretation(monkeypatch):
    monkeypatch.setattr(
        "app.domain.services.chat_analysis_intent_service."
        "ChatAnalysisIntentService.is_data_interpretation_request",
        lambda *_a, **_k: True,
    )
    monkeypatch.setattr(
        "app.application.services.chat_conversation_context_service."
        "ChatConversationContextService.has_recent_tool_data",
        lambda *_a, **_k: True,
    )

    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="comparar com ano anterior no mesmo periodo",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[{"role": "assistant", "content": "ROL"}],
        workspace_context={
            "workingMemory": {
                "lastAction": {"path": "/financial/rol"},
                "lastResultExcerpt": {"title": "ROL"},
            },
            "turnGrounding": {
                "status": "grounded",
                "stage": "grounded_revise_query",
                "followUp": {
                    "continuityMode": "consume_last_action",
                    "requiresLastActionReexec": True,
                },
            },
        },
    )

    assert flags.skip_tools_for_data_interpretation is False


def test_resolve_skip_tool_flags_for_session_review():
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="o que me diz sobre a conversa?",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[
            {"role": "user", "content": "estoque 10080055"},
            {"role": "assistant", "content": "Saldo total"},
        ],
    )

    assert flags.skip_tools_for_session_review is True
    assert ChatTurnPreparationToolRoutingService.should_skip_tools(
        canvas_action=None,
        canvas_operational_update=False,
        pre_capability_answer=None,
        missing_product_code_answer=None,
        ambiguous_period_answer=None,
        missing_date_answer=None,
        common_chat_operational_answer=None,
        routing_disambiguation_answer=None,
        learning_term_confirmation_answer=None,
        interpretation_without_data_answer=None,
        skip_flags=flags,
        small_talk_direct=None,
        utility_direct=None,
        web_save_sources_direct=None,
        project_sources_direct=None,
        web_post_search_direct=None,
        attachment_welcome_direct=None,
        unclear_direct=None,
        text_task_pure=False,
    ) is True


def test_should_skip_tools_for_small_talk():
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="oi",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[],
    )

    assert ChatTurnPreparationToolRoutingService.should_skip_tools(
        canvas_action=None,
        canvas_operational_update=False,
        pre_capability_answer=None,
        missing_product_code_answer=None,
        ambiguous_period_answer=None,
        missing_date_answer=None,
        common_chat_operational_answer=None,
        routing_disambiguation_answer=None,
        learning_term_confirmation_answer=None,
        interpretation_without_data_answer=None,
        skip_flags=flags,
        small_talk_direct="Olá! Como posso ajudar?",
        utility_direct=None,
        web_save_sources_direct=None,
        project_sources_direct=None,
        web_post_search_direct=None,
        attachment_welcome_direct=None,
        unclear_direct=None,
        text_task_pure=False,
    )


def test_run_tool_phase_skips_tools_for_text_task():
    request = MagicMock()
    request.attachment_ids = None
    pipeline_stages = ["ingress"]
    pipeline_timings = ChatPipelineTimings()
    build_tool_context = MagicMock()

    from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
        ChatTurnPreparationOperationalGuards,
        ChatTurnPreparationSkipToolFlags,
    )

    result = ChatTurnPreparationToolRoutingService.run_tool_phase(
        message="corrija este texto",
        request=request,
        history_source=[],
        workspace_context={},
        conversation_context="",
        pipeline_stages=pipeline_stages,
        pipeline_timings=pipeline_timings,
        canvas_action=None,
        canvas_operational_update=False,
        pre_capability_answer=None,
        operational_guards=ChatTurnPreparationOperationalGuards(None, None, None, None),
        routing_disambiguation_answer=None,
        learning_term_confirmation_answer=None,
        interpretation_without_data_answer=None,
        skip_flags=ChatTurnPreparationSkipToolFlags(False, False, False, False, False, False, False, False, False, []),
        small_talk_direct=None,
        utility_direct=None,
        web_save_sources_direct=None,
        project_sources_direct=None,
        web_post_search_direct=None,
        attachment_welcome_direct=None,
        unclear_direct=None,
        text_task_pure=True,
        fast_path=False,
        operational_optimize=False,
        analysis_mode=False,
        build_tool_context=build_tool_context,
        maybe_extend_tool_context=MagicMock(),
        max_external_action_calls=None,
    )

    assert result.tool_calls == []
    assert "text_task" in pipeline_stages
    build_tool_context.assert_not_called()


def test_run_tool_phase_invokes_build_tool_context_with_request_once():
    from functools import partial

    from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
        ChatTurnPreparationOperationalGuards,
        ChatTurnPreparationSkipToolFlags,
    )

    request = MagicMock()
    request.attachment_ids = None
    request.access_token = "token"
    calls: list[tuple] = []

    def build_tool_context(call_request, **kwargs):
        calls.append((call_request, kwargs))
        return {"context": "ctx", "toolCalls": [{"name": "get_product"}]}

    result = ChatTurnPreparationToolRoutingService.run_tool_phase(
        message="me fale do produto 10080045",
        request=request,
        history_source=[],
        workspace_context={"capabilities": {"actions": True}},
        conversation_context="",
        pipeline_stages=[],
        pipeline_timings=ChatPipelineTimings(),
        canvas_action=None,
        canvas_operational_update=False,
        pre_capability_answer=None,
        operational_guards=ChatTurnPreparationOperationalGuards(None, None, None, None),
        routing_disambiguation_answer=None,
        learning_term_confirmation_answer=None,
        interpretation_without_data_answer=None,
        skip_flags=ChatTurnPreparationSkipToolFlags(False, False, False, False, False, False, False, False, False, []),
        small_talk_direct=None,
        utility_direct=None,
        web_save_sources_direct=None,
        project_sources_direct=None,
        web_post_search_direct=None,
        attachment_welcome_direct=None,
        unclear_direct=None,
        text_task_pure=False,
        fast_path=False,
        operational_optimize=False,
        analysis_mode=False,
        build_tool_context=partial(build_tool_context, agent_context={"id": str(uuid4())}),
        maybe_extend_tool_context=lambda **kwargs: kwargs["tool_context"],
        max_external_action_calls=None,
    )

    assert len(calls) == 1
    assert calls[0][0] is request
    assert result.tool_calls == [{"name": "get_product"}]


def test_run_tool_phase_skips_tools_for_assistant_identity_question():
    from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
        ChatTurnPreparationOperationalGuards,
        ChatTurnPreparationSkipToolFlags,
    )

    request = MagicMock()
    request.attachment_ids = None
    pipeline_stages = ["ingress"]
    build_tool_context = MagicMock()

    result = ChatTurnPreparationToolRoutingService.run_tool_phase(
        message="quem é vc?",
        request=request,
        history_source=[],
        workspace_context={},
        conversation_context="",
        pipeline_stages=pipeline_stages,
        pipeline_timings=ChatPipelineTimings(),
        canvas_action=None,
        canvas_operational_update=False,
        pre_capability_answer=None,
        operational_guards=ChatTurnPreparationOperationalGuards(None, None, None, None),
        routing_disambiguation_answer=None,
        learning_term_confirmation_answer=None,
        interpretation_without_data_answer=None,
        skip_flags=ChatTurnPreparationSkipToolFlags(False, True, False, False, False, False, False, False, False, []),
        small_talk_direct=None,
        utility_direct=None,
        web_save_sources_direct=None,
        project_sources_direct=None,
        web_post_search_direct=None,
        attachment_welcome_direct=None,
        unclear_direct=None,
        text_task_pure=False,
        fast_path=False,
        operational_optimize=False,
        analysis_mode=False,
        build_tool_context=build_tool_context,
        maybe_extend_tool_context=MagicMock(),
        max_external_action_calls=None,
    )

    assert result.tool_calls == []
    assert "assistant_identity_shortcut" in pipeline_stages
    build_tool_context.assert_not_called()


def test_resolve_skip_tool_flags_for_common_chat_without_active_agent():
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="o que vc pensa sobre o Brasil?",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[],
        workspace_context={
            "userActivatedAgent": False,
            "actionsEnabled": False,
        },
    )

    assert flags.skip_tools_for_inactive_agent is True


@patch(
    "app.domain.services.chat_web_search_intent_service.ChatWebSearchIntentService.is_feature_enabled",
    return_value=True,
)
def test_resolve_skip_tool_flags_allows_web_augment_in_common_chat(_web_enabled):
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="o que vc pensa sobre o Brasil?",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[],
        workspace_context={
            "userActivatedAgent": False,
            "actionsEnabled": False,
        },
    )

    assert flags.skip_tools_for_inactive_agent is False


def test_resolve_skip_tool_flags_allows_tv_surface_in_common_chat():
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="crie um slide",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[],
        workspace_context={
            "userActivatedAgent": False,
            "actionsEnabled": False,
            "skills": {"tvDashboardCopilot": True},
            "tvDashboardHostContext": {
                "surface": "tv-dashboard",
                "playlistId": "pl-1",
            },
        },
    )

    assert flags.skip_tools_for_inactive_agent is False


def test_tv_surface_mutation_bypasses_operational_parameter_guards():
    guards = ChatTurnPreparationToolRoutingService.resolve_operational_guards(
        message="adicione um modelo de dados de OEE",
        history_source=[],
        conversation_context="",
        working_memory_snapshot={},
        workspace_context={
            "userActivatedAgent": False,
            "actionsEnabled": False,
            "skills": {"tvDashboardCopilot": True},
            "tvDashboardHostContext": {
                "surface": "tv-dashboard",
                "playlistId": "pl-1",
                "slideId": "sl-1",
            },
        },
        canvas_action=None,
        pre_capability_answer=None,
        analysis_mode=False,
        text_task_pure=False,
    )

    assert guards.missing_product_code_answer is None
    assert guards.ambiguous_period_answer is None
    assert guards.missing_date_answer is None
    assert guards.common_chat_operational_answer is None


def test_resolve_skip_tool_flags_for_project_sources_content_follow_up():
    inventory = [
        {
            "projectSourceId": "doc-1",
            "title": "Manual homologação DELPI",
            "ordinal": 1,
        }
    ]
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="resuma o conteúdo do primeiro arquivo",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[
            {
                "role": "assistant",
                "metadata": {
                    "contextSnapshot": {"lastProjectSourcesInventory": inventory},
                },
            }
        ],
        workspace_context={},
    )

    assert flags.skip_tools_for_project_sources_content is True


def test_skip_tools_false_for_grounded_revise_query():
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="somente da filial 01",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[],
        workspace_context={
            "turnGrounding": {
                "status": "grounded",
                "stage": "grounded_revise_query",
                "excerpt": {"title": "ROL", "preview": "total", "rowCount": 1},
            },
            "workingMemory": {
                "lastResultExcerpt": {"title": "ROL", "preview": "total", "rowCount": 1},
                "lastAction": {
                    "path": "/financial/rol",
                    "params": {"start_date": "01-08-2026", "end_date": "28-08-2026"},
                },
            },
        },
    )
    assert flags.skip_tools_for_grounded_narrate is False


def test_skip_tools_true_for_grounded_challenge():
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="o rol de uma unidade não pode ser igual ao total",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[],
        workspace_context={
            "turnGrounding": {
                "status": "grounded",
                "stage": "grounded_challenge_result",
                "excerpt": {"title": "ROL", "preview": "total", "rowCount": 1},
            },
            "workingMemory": {
                "lastResultExcerpt": {"title": "ROL", "preview": "total", "rowCount": 1},
                "lastAction": {
                    "path": "/financial/rol",
                    "params": {"start_date": "01-08-2026", "end_date": "28-08-2026"},
                },
            },
        },
    )
    assert flags.skip_tools_for_grounded_narrate is True


def test_missing_date_suppressed_for_challenge_follow_up():
    guards = ChatTurnPreparationToolRoutingService.resolve_operational_guards(
        message="o rol de uma unidade não pode ser igual ao total",
        history_source=[],
        conversation_context="",
        working_memory_snapshot={
            "lastAction": {
                "path": "/financial/rol",
                "params": {"start_date": "01-08-2026", "end_date": "28-08-2026"},
            }
        },
        workspace_context={
            "turnGrounding": {
                "status": "grounded",
                "stage": "grounded_challenge_result",
                "followUp": {"decision": "challenge_last_result"},
            }
        },
        canvas_action=None,
        pre_capability_answer=None,
        analysis_mode=False,
        text_task_pure=False,
    )
    assert guards.missing_date_answer is None
