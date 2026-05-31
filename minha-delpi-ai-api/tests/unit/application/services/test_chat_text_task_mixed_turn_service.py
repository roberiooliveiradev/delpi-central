from app.application.services.chat_text_task_mixed_turn_service import (
    ChatTextTaskMixedTurnService,
)


def test_build_snapshot_for_mixed_message():
    snapshot = ChatTextTaskMixedTurnService.build_snapshot(
        message="consulte o estoque e escreva um e-mail",
        pipeline_stages=["text_task_mixed", "email_operational"],
        tool_context={"operationalEmailDraft": {"text": "Assunto: Teste"}},
    )

    assert snapshot is not None
    assert snapshot["operational"] is True
    assert snapshot["draftAttached"] is True
    assert snapshot["textCategory"] == "email"


def test_pure_text_returns_none():
    assert (
        ChatTextTaskMixedTurnService.build_snapshot(
            message="corrija este texto",
        )
        is None
    )
