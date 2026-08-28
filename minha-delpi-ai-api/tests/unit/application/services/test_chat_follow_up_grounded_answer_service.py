from app.application.services.chat_follow_up_grounded_answer_service import (
    ChatFollowUpGroundedAnswerService,
)


_EXCERPT = {
    "title": "ROL do mês",
    "preview": "ROL consolidado: R$ 1.000.000",
    "rowCount": 1,
}


def test_challenge_answer_uses_excerpt_without_asking_period():
    answer = ChatFollowUpGroundedAnswerService.build_challenge_answer(
        workspace_context={
            "turnGrounding": {"stage": "grounded_challenge_result", "excerpt": _EXCERPT},
            "workingMemory": {
                "lastResultExcerpt": _EXCERPT,
                "lastAction": {
                    "path": "/financial/rol",
                    "params": {"start_date": "01-08-2026", "end_date": "28-08-2026"},
                },
            },
        }
    )
    assert answer
    assert "1.000.000" in answer or "ROL" in answer
    assert "período" not in answer.lower() or "Período da última" in answer
    assert "preciso" not in answer.lower()
    assert ChatFollowUpGroundedAnswerService.challenge_suggestion_items()


def test_clarify_answer_asks_branch():
    answer = ChatFollowUpGroundedAnswerService.build_clarify_answer(
        workspace_context={
            "turnGrounding": {
                "stage": "grounded_clarify_slot",
                "followUp": {"clarifySlot": "branch"},
            }
        }
    )
    assert answer
    assert "filial" in answer.lower()


def test_revise_ack_mentions_branch():
    ack = ChatFollowUpGroundedAnswerService.build_revise_ack(
        parameters={"branch": "01", "start_date": "01-08-2026", "end_date": "28-08-2026"}
    )
    assert ack
    assert "01" in ack
