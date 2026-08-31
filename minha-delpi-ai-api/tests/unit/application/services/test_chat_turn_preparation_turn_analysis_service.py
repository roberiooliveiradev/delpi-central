from unittest.mock import MagicMock

from app.application.services.chat_turn.chat_turn_preparation_turn_analysis_service import (
    ChatTurnPreparationTurnAnalysisService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_turn_analysis_service import ChatTurnAnalysisResult

configure_domain_infrastructure_ports()


def test_maybe_analyze_skips_when_direct_answer_already_set():
    ChatTurnPreparationTurnAnalysisService.reset_ran()
    outcome = ChatTurnPreparationTurnAnalysisService.maybe_analyze(
        message="programação",
        request=MagicMock(response_mode="normal", attachment_ids=[]),
        workspace_context={"allowedActionIds": []},
        history_source=[],
        pipeline_stages=["unclear_request"],
        has_direct_answer=True,
    )

    assert outcome.result is None
    assert outcome.skip_tools is False
    assert not ChatTurnPreparationTurnAnalysisService.ran_this_turn()


def test_maybe_analyze_skips_when_tools_already_skipped(monkeypatch):
    ChatTurnPreparationTurnAnalysisService.reset_ran()
    called = {"classify": False}

    def _fail_classify(*args, **kwargs):
        called["classify"] = True
        raise AssertionError("IntentRouter.classify não deve rodar com tools_already_skipped")

    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_turn_preparation_turn_analysis_service.ChatIntentRouterService.classify",
        _fail_classify,
    )
    outcome = ChatTurnPreparationTurnAnalysisService.maybe_analyze(
        message="como vc se chama?",
        request=MagicMock(response_mode="normal", attachment_ids=[]),
        workspace_context={"allowedActionIds": []},
        history_source=[],
        pipeline_stages=["assistant_identity_shortcut"],
        has_direct_answer=False,
        tools_already_skipped=True,
    )

    assert outcome.result is None
    assert called["classify"] is False
    assert not ChatTurnPreparationTurnAnalysisService.ran_this_turn()


def test_maybe_analyze_clarify_sets_direct_answer(monkeypatch):
    ChatTurnPreparationTurnAnalysisService.reset_ran()

    def _fake_analyze(**kwargs):
        return ChatTurnAnalysisResult(
            decision="clarify",
            clarify_key="ambiguous_domain",
            reason="vague_term",
            source="test",
        )

    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_turn_preparation_turn_analysis_service.ChatTurnAnalysisService.analyze",
        _fake_analyze,
    )
    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_turn_preparation_turn_analysis_service.ChatTurnAnalysisService.should_analyze",
        lambda **kwargs: True,
    )

    outcome = ChatTurnPreparationTurnAnalysisService.maybe_analyze(
        message="xyzzy-nonsense",
        request=MagicMock(response_mode="normal", attachment_ids=[]),
        workspace_context={"allowedActionIds": []},
        history_source=[],
        pipeline_stages=[],
        has_direct_answer=False,
        llm_gateway=MagicMock(),
    )

    assert outcome.result is not None
    assert outcome.result.decision == "clarify"
    assert outcome.direct_answer
    assert outcome.skip_tools is True
    assert ChatTurnPreparationTurnAnalysisService.ran_this_turn()
