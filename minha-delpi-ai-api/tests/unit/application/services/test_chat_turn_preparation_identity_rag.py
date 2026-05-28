"""Perguntas de identidade do assistente: resposta canônica rápida (sem LLM)."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)


def _prepare(
    message: str,
    *,
    skills: dict | None = None,
    identity_direct_enabled: bool = True,
) -> object:
    session = MagicMock()
    session.id = uuid4()
    user_id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {
        "context": "Trecho irrelevante se chamado.",
        "sources": [{"title": "Doc"}],
    }

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    import app.application.services.chat_turn.chat_turn_preparation_service as prep_module

    original = prep_module.Settings.CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED
    prep_module.Settings.CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED = identity_direct_enabled
    try:
        prepared = service.prepare(
            message=message,
            request=request,
            session=session,
            user_id=user_id,
            workspace_context={
                "skills": skills or {"companyKnowledge": True},
                "allowedActionIds": [],
                "capabilities": {},
            },
            attachments=[],
            previous_messages=[],
            history_source=[],
            build_tool_context=lambda *args, **kwargs: {
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": {},
            },
            maybe_extend_tool_context=lambda **kwargs: kwargs["tool_context"],
            prepare_history=lambda history: ("", list(history)),
            history_keep=12,
            fast_path_enabled=True,
            fast_path_max_chars=30,
            resolve_user_identity_answer=lambda msg: None,
            resolve_capabilities_answer=lambda msg: None,
        )
    finally:
        prep_module.Settings.CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED = original

    return prepared, rag_context_service


def test_identity_question_uses_direct_answer_and_skips_rag():
    prepared, rag_context_service = _prepare("quem te criou?")

    assert prepared.direct_answer
    assert "modelo de linguagem" in prepared.direct_answer.lower()
    assert prepared.skip_rag is True
    assert prepared.rag["context"] == ""
    rag_context_service.build_context.assert_not_called()


def test_identity_question_can_use_rag_when_direct_disabled(monkeypatch):
    prepared, rag_context_service = _prepare(
        "quem te criou?",
        identity_direct_enabled=False,
    )

    assert prepared.direct_answer is None
    assert prepared.skip_rag is False
    rag_context_service.build_context.assert_called()


def test_identity_question_skips_rag_on_fast_path_without_company_skill():
    prepared, rag_context_service = _prepare(
        "quem é vc?",
        skills={"companyKnowledge": False},
    )

    assert prepared.direct_answer
    assert prepared.skip_rag is True
    rag_context_service.build_context.assert_not_called()
