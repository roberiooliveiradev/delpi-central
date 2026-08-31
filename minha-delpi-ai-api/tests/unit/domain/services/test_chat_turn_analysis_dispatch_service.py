"""Despacho de fluxos a partir da turn analysis."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_turn_analysis_dispatch_service import (
    ChatTurnAnalysisDispatchService,
)
from app.domain.services.chat_turn_analysis_service import ChatTurnAnalysisResult

configure_domain_infrastructure_ports()


def test_normalize_intent_aliases():
    assert ChatTurnAnalysisDispatchService.normalize_intent("assistant_identity") == "identity"
    assert ChatTurnAnalysisDispatchService.normalize_intent("who_are_you") == "identity"
    assert ChatTurnAnalysisDispatchService.normalize_intent("correct_text") == "text_correction"


def test_dispatch_identity_builds_direct_without_pattern_match():
    result = ChatTurnAnalysisResult(
        decision="narrate",
        intent="identity",
        sub_intent="who",
        reason="typo_name_question",
    )
    dispatch = ChatTurnAnalysisDispatchService.resolve(
        result,
        message="como u posso te chamar?",
        workspace_context={},
        operational_tools_enabled=False,
    )
    assert dispatch is not None
    assert dispatch.kind == "identity"
    assert dispatch.skip_rag is True
    assert dispatch.skip_tools is True
    assert dispatch.force_assistant_identity_skip is True
    assert dispatch.direct_answer
    assert "delpi" in dispatch.direct_answer.lower() or "assistente" in dispatch.direct_answer.lower()


def test_dispatch_small_talk():
    result = ChatTurnAnalysisResult(
        decision="narrate",
        intent="small_talk",
        sub_intent="greeting",
        reason="typo_greeting",
    )
    dispatch = ChatTurnAnalysisDispatchService.resolve(
        result,
        message="td bem?",
        workspace_context={},
    )
    assert dispatch is not None
    assert dispatch.kind == "small_talk"
    assert dispatch.direct_answer
    assert dispatch.skip_rag is True


def test_dispatch_text_correction_mode():
    result = ChatTurnAnalysisResult(
        decision="narrate",
        intent="text_correction",
        reason="typo_correct",
    )
    dispatch = ChatTurnAnalysisDispatchService.resolve(
        result,
        message="coreja o texto: ola",
        workspace_context={},
    )
    assert dispatch is not None
    assert dispatch.kind == "text_correction"
    assert dispatch.text_correction_mode is True
    assert dispatch.skip_rag is True


def test_dispatch_execute_without_agent_forces_guidance():
    result = ChatTurnAnalysisResult(
        decision="execute",
        intent="operational_query",
        action_ids=("get_financial_rol",),
        reason="rol_query",
    )
    dispatch = ChatTurnAnalysisDispatchService.resolve(
        result,
        message="qual o rol filial 01",
        workspace_context={},
        operational_tools_enabled=False,
    )
    assert dispatch is not None
    assert dispatch.kind == "execute_needs_agent"
    assert dispatch.force_common_chat_guidance is True
    assert dispatch.clear_action_ids is True


def test_dispatch_execute_with_agent():
    result = ChatTurnAnalysisResult(
        decision="execute",
        intent="operational_query",
        action_ids=("get_financial_rol",),
        reason="rol_query",
    )
    dispatch = ChatTurnAnalysisDispatchService.resolve(
        result,
        message="qual o rol filial 01",
        workspace_context={"agent": {"id": "x"}},
        operational_tools_enabled=True,
    )
    assert dispatch is not None
    assert dispatch.kind == "execute"
    assert dispatch.skip_tools is False


def test_dispatch_clarify():
    result = ChatTurnAnalysisResult(
        decision="clarify",
        clarify_key="default",
        reason="vague",
    )
    dispatch = ChatTurnAnalysisDispatchService.resolve(
        result,
        message="isso",
        workspace_context={},
    )
    assert dispatch is not None
    assert dispatch.kind == "clarify"
    assert dispatch.direct_answer
