"""Perguntas de identidade do assistente: rota meta LLM (sem RAG)."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)
from tests.support.chat_intelligence_runtime import (
    build_chat_intelligence_runtime_mock,
    patch_resolve_chat_intelligence_runtime,
)


def _prepare(
    message: str,
    *,
    skills: dict | None = None,
    identity_direct_enabled: bool = True,
    monkeypatch=None,
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

    if monkeypatch is not None:
        patch_resolve_chat_intelligence_runtime(
            monkeypatch,
            build_chat_intelligence_runtime_mock(
                assistant_identity_direct_enabled=identity_direct_enabled,
            ),
        )

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

    return prepared, rag_context_service


def test_identity_question_uses_meta_synthesis_and_skips_rag():
    prepared, rag_context_service = _prepare("quem te criou?")

    assert prepared.direct_answer is None
    assert prepared.tool_context.get("metaLlmSynthesis") is True
    assert "modelo de linguagem" in str(
        prepared.tool_context.get("metaSynthesisFacts") or ""
    ).lower()
    assert prepared.skip_rag is True
    assert "assistant_identity_shortcut" in prepared.pipeline_stages
    rag_context_service.build_context.assert_not_called()


def test_identity_question_can_use_rag_when_direct_disabled(monkeypatch):
    prepared, rag_context_service = _prepare(
        "quem te criou?",
        identity_direct_enabled=False,
        monkeypatch=monkeypatch,
    )

    assert prepared.tool_context.get("metaLlmSynthesis") is True
    assert prepared.skip_rag is True
    rag_context_service.build_context.assert_not_called()


def test_identity_question_skips_rag_on_fast_path_without_company_skill():
    prepared, rag_context_service = _prepare(
        "quem é vc?",
        skills={"companyKnowledge": False},
    )

    assert prepared.tool_context.get("metaLlmSynthesis") is True
    assert prepared.skip_rag is True
    rag_context_service.build_context.assert_not_called()
