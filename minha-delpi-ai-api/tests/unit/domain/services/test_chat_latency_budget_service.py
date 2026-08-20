from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_latency_budget_service import ChatLatencyBudgetService
from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)

configure_domain_infrastructure_ports()


def test_latency_target_sec_from_response_modes_json():
    assert ChatResponseModeContentService.latency_target_sec("fast", default=99) == 3
    assert ChatResponseModeContentService.latency_target_sec("normal", default=99) == 5
    assert ChatResponseModeContentService.latency_target_sec("thinker", default=99) == 15
    assert ChatLatencyBudgetService.latency_target_sec("rapida") == 3


def test_skip_optional_rag_when_over_budget():
    skip, stage = ChatLatencyBudgetService.maybe_skip_optional_documentary_rag(
        skip_rag=False,
        elapsed_sec=6.0,
        response_mode="normal",
        tool_context={"responseMode": "normal"},
        requires_documentary_rag=False,
    )

    assert skip is True
    assert stage == "rag"


def test_keep_rag_when_documentary_required():
    skip, stage = ChatLatencyBudgetService.maybe_skip_optional_documentary_rag(
        skip_rag=False,
        elapsed_sec=30.0,
        response_mode="fast",
        tool_context={},
        requires_documentary_rag=True,
    )

    assert skip is False
    assert stage is None


def test_keep_rag_when_tool_results_need_synthesis():
    skip, stage = ChatLatencyBudgetService.maybe_skip_optional_documentary_rag(
        skip_rag=False,
        elapsed_sec=30.0,
        response_mode="fast",
        tool_context={
            "responseModeEffect": "llm_synthesis",
            "toolCalls": [{"name": "execute_external_action"}],
            "directAnswer": None,
        },
        requires_documentary_rag=False,
    )

    assert skip is False
    assert stage is None


def test_message_search_lookback_reduced_when_degraded():
    reduced = ChatLatencyBudgetService.resolve_message_search_lookback(
        80,
        degraded_stages=["message_search"],
    )

    assert reduced == 40
    assert ChatLatencyBudgetService.resolve_message_search_lookback(80) == 80


def test_append_degraded_stages_on_tool_context():
    tool_context: dict = {}
    ChatLatencyBudgetService.append_degraded_stage(tool_context, "rag")
    ChatLatencyBudgetService.maybe_mark_message_search_degraded(
        elapsed_sec=10.0,
        response_mode="normal",
        tool_context=tool_context,
    )

    assert tool_context["degradedStages"] == ["rag", "message_search"]
