from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.domain.services.chat_turn_mode_service import ChatTurnModeService


def test_turn_mode_consume_prior_for_drawing_direct_answer():
    mode = ChatTurnModeService.resolve(
        message="confirmar revisão manual",
        tool_context={"drawingAnalysisMode": True, "directAnswer": "ok"},
        direct_answer="ok",
        pipeline_stages=["drawing_analysis"],
    )

    assert mode == ChatTurnModeService.CONSUME_PRIOR
    assert ChatTurnModeService.should_skip_llm(mode)
    assert ChatTurnModeService.should_skip_agentic(mode)


def test_turn_mode_ask_slot_for_missing_required_parameter():
    mode = ChatTurnModeService.resolve(
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": False,
                    "errorKind": "missing_required_parameter",
                    "missingParameter": "code",
                },
            }
        ],
    )

    assert mode == ChatTurnModeService.ASK_SLOT


def test_response_mode_honors_turn_mode_consume_prior():
    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="confirmar revisão",
        response_mode="normal",
        direct_answer="Relatório revisado.",
        skip_rag=True,
        tool_calls=[],
        tool_context={"drawingAnalysisMode": True},
        pipeline_stages=["drawing_analysis"],
    )

    assert direct == "Relatório revisado."
    assert effect == "simple_direct"
    assert skip_rag is True
