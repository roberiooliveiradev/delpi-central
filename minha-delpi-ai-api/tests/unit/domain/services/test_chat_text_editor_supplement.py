"""Regressão ChatTextEditorSupplementService — playbook editor textual."""

from app.domain.services.chat_text_editor_supplement_service import ChatTextEditorSupplementService
from app.domain.services.chat_text_task_service import ChatTextTaskService


def test_build_block_for_letter():
    ctx = ChatTextTaskService.classify("crie uma carta formal")

    block = ChatTextEditorSupplementService.build_block(ctx)

    assert block is not None
    assert "Carta formal" in block


def test_suggest_canvas_for_long_email():
    answer = " ".join(["linha"] * 90)

    assert ChatTextEditorSupplementService.suggest_canvas_for_subtype(
        "text_email_create",
        answer=answer,
    )


def test_metadata_includes_text_assistant():
    payload = ChatTextTaskService.build_text_task_metadata(
        message="explique RBAC como se eu tivesse 5 anos",
    )

    assert payload is not None
    assert payload["textAssistant"]["intent"] == "text.eli5"
