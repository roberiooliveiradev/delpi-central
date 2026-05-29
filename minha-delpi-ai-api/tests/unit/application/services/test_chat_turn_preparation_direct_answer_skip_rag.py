"""Resposta direta no tool_context força skip_rag (11.2.1)."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)


def test_direct_answer_in_tool_context_forces_skip_rag():
    session = MagicMock()
    session.id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    build_tool_context = MagicMock(
        return_value={
            "context": "",
            "toolCalls": [],
            "directAnswer": "Resposta operacional direta.",
            "nativeToolCalling": {},
        }
    )

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    prepared = service.prepare(
        message="qualquer",
        request=request,
        session=session,
        user_id=uuid4(),
        workspace_context={},
        attachments=[],
        previous_messages=[],
        history_source=[],
        build_tool_context=build_tool_context,
        maybe_extend_tool_context=lambda **kwargs: kwargs["tool_context"],
        prepare_history=lambda history: ("", list(history)),
        history_keep=12,
        fast_path_enabled=True,
        fast_path_max_chars=30,
        resolve_user_identity_answer=lambda msg: None,
        resolve_capabilities_answer=lambda msg: None,
    )

    assert prepared.direct_answer == "Resposta operacional direta."
    assert prepared.skip_rag is True
    assert "skip_rag" in prepared.pipeline_stages
    assert "direct_answer" in prepared.pipeline_stages
    rag_context_service.build_context.assert_not_called()


def test_small_talk_uses_direct_answer_and_skips_rag_and_tools():
    session = MagicMock()
    session.id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    build_tool_context = MagicMock()
    maybe_extend_tool_context = MagicMock()

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    prepared = service.prepare(
        message="ola",
        request=request,
        session=session,
        user_id=uuid4(),
        workspace_context={},
        attachments=[],
        previous_messages=[],
        history_source=[],
        build_tool_context=build_tool_context,
        maybe_extend_tool_context=maybe_extend_tool_context,
        prepare_history=lambda history: ("", list(history)),
        history_keep=12,
        fast_path_enabled=True,
        fast_path_max_chars=30,
        resolve_user_identity_answer=lambda msg: None,
        resolve_capabilities_answer=lambda msg: None,
    )

    assert prepared.direct_answer
    assert "ajudar" in prepared.direct_answer.lower()
    assert prepared.skip_rag is True
    assert "small_talk" in prepared.pipeline_stages
    assert "skip_rag" in prepared.pipeline_stages
    build_tool_context.assert_not_called()
    maybe_extend_tool_context.assert_not_called()
    rag_context_service.build_context.assert_not_called()
