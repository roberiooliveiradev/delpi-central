"""Fallback pós-RAG: web quando a base interna não trouxe trechos."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


def _prepare_with_empty_rag(
    message: str,
    *,
    run_post_rag_web_fallback=None,
):
    session = MagicMock()
    session.id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {
        "context": "",
        "sources": [],
    }

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    prepared = service.prepare(
        message=message,
        request=request,
        session=session,
        user_id=uuid4(),
        workspace_context={
            "skills": {"companyKnowledge": True},
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
        run_post_rag_web_fallback=run_post_rag_web_fallback,
    )

    return prepared, rag_context_service


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_post_rag_web_fallback_applies_for_factual_question(_enabled):
    fallback_context = {
        "context": "Paris é a capital da França.",
        "toolCalls": [
            {
                "name": "web_search",
                "arguments": {"query": "capital da frança dados atuais internet"},
            }
        ],
        "webSources": [{"title": "Wikipedia", "url": "https://example.com/fr"}],
        "nativeToolCalling": {},
    }
    calls = {"count": 0}

    def _run_fallback():
        calls["count"] += 1
        return fallback_context

    prepared, _ = _prepare_with_empty_rag(
        "qual a capital da frança?",
        run_post_rag_web_fallback=_run_fallback,
    )

    assert calls["count"] == 1
    assert "rag_web_fallback" in prepared.pipeline_stages
    assert "tools" in prepared.pipeline_stages
    assert any(call.get("name") == "web_search" for call in prepared.tool_calls)
    assert prepared.tool_context.get("context") == fallback_context["context"]
    assert prepared.sources == fallback_context["webSources"]


def test_post_rag_web_fallback_skips_when_rag_has_sources():
    calls = {"count": 0}

    def _run_fallback():
        calls["count"] += 1
        return None

    session = MagicMock()
    session.id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {
        "context": "Trecho interno.",
        "sources": [{"title": "Norma interna"}],
    }

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    prepared = service.prepare(
        message="qual a capital da frança?",
        request=request,
        session=session,
        user_id=uuid4(),
        workspace_context={
            "skills": {"companyKnowledge": True},
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
        run_post_rag_web_fallback=_run_fallback,
    )

    assert calls["count"] == 0
    assert "rag_web_fallback" not in prepared.pipeline_stages


def test_post_rag_web_fallback_skips_operational_rewrite():
    calls = {"count": 0}

    def _run_fallback():
        calls["count"] += 1
        return None

    prepared, _ = _prepare_with_empty_rag(
        "reescreva este texto para ficar mais formal",
        run_post_rag_web_fallback=_run_fallback,
    )

    assert calls["count"] == 0
    assert "rag_web_fallback" not in prepared.pipeline_stages
