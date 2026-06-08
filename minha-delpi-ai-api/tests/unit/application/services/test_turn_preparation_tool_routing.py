from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
    ChatTurnPreparationToolRoutingService,
)


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
        skip_flags=ChatTurnPreparationSkipToolFlags(False, False, False, []),
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
