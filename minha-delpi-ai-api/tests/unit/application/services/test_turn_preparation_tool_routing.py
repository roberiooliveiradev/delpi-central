from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
    ChatTurnPreparationToolRoutingService,
)


def test_resolve_skip_tool_flags_for_assistant_identity_question():
    flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
        message="quem é vc?",
        request=MagicMock(attachment_ids=None, access_token=None),
        history_source=[],
    )

    assert flags.skip_tools_for_assistant_identity is True
    assert flags.skip_tools_for_user_identity is False


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
        routing_disambiguation_answer=None,
        interpretation_without_data_answer=None,
        skip_flags=flags,
        small_talk_direct="Olá! Como posso ajudar?",
        utility_direct=None,
        web_save_sources_direct=None,
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
        operational_guards=ChatTurnPreparationOperationalGuards(None, None),
        routing_disambiguation_answer=None,
        interpretation_without_data_answer=None,
        skip_flags=ChatTurnPreparationSkipToolFlags(False, False, False, False, []),
        small_talk_direct=None,
        utility_direct=None,
        web_save_sources_direct=None,
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
        operational_guards=ChatTurnPreparationOperationalGuards(None, None),
        routing_disambiguation_answer=None,
        interpretation_without_data_answer=None,
        skip_flags=ChatTurnPreparationSkipToolFlags(False, False, False, False, []),
        small_talk_direct=None,
        utility_direct=None,
        web_save_sources_direct=None,
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
        operational_guards=ChatTurnPreparationOperationalGuards(None, None),
        routing_disambiguation_answer=None,
        interpretation_without_data_answer=None,
        skip_flags=ChatTurnPreparationSkipToolFlags(False, True, False, False, []),
        small_talk_direct=None,
        utility_direct=None,
        web_save_sources_direct=None,
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
