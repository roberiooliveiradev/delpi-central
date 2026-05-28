"""Perguntas de identidade do assistente devem passar pelo RAG + LLM."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)


def _prepare(message: str, *, skills: dict | None = None) -> object:
    session = MagicMock()
    session.id = uuid4()
    user_id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {
        "context": "Trecho do Arquiteto do Código.",
        "sources": [{"title": "O Arquiteto do Código"}],
    }

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    return service.prepare(
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


def test_identity_question_does_not_use_canned_direct_answer():
    prepared = _prepare("quem te criou?")

    assert prepared.direct_answer is None
    assert prepared.skip_rag is False
    assert prepared.rag["context"]
    assert prepared.sources


def test_identity_question_runs_rag_even_on_fast_path_without_company_skill():
    prepared = _prepare("quem é vc?", skills={"companyKnowledge": False})

    assert prepared.direct_answer is None
    assert prepared.skip_rag is False
