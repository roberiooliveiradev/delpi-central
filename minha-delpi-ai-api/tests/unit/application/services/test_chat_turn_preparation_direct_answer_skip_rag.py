"""Resposta direta no tool_context força skip_rag (11.2.1)."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)


def test_direct_answer_in_tool_context_forces_skip_rag(
    presentation_only_shortcut_enabled,
):
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
        workspace_context={"userActivatedAgent": True, "actionsEnabled": True},
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
    assert "tools" in prepared.pipeline_stages
    rag_context_service.build_context.assert_not_called()


def test_operational_rich_presentation_replaces_existing_direct_answer(
    presentation_only_shortcut_enabled,
):
    session = MagicMock()
    session.id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "statusCode": 200,
                "path": "/commercial/billing",
                "presentation": {
                    "type": "kpi",
                    "title": "Faturamento comercial",
                    "items": [{"label": "Total", "value": "R$ 1,00"}],
                },
            },
        }
    ]
    build_tool_context = MagicMock(
        return_value={
            "context": "",
            "toolCalls": tool_calls,
            "directAnswer": "| Filial | Valor |\n| --- | --- |\n| 01 | R$ 1,00 |",
            "nativeToolCalling": {},
            "skipRag": True,
        }
    )

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    prepared = service.prepare(
        message="resultado da consulta",
        request=request,
        session=session,
        user_id=uuid4(),
        workspace_context={
            "userActivatedAgent": True,
            "actionsEnabled": True,
            "allowedActionIds": ["get_commercial_billing"],
        },
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

    assert prepared.direct_answer == "Faturamento comercial"
    assert prepared.skip_rag is True
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
    assert "resolver" in prepared.direct_answer.lower()
    assert prepared.skip_rag is True
    assert "small_talk" in prepared.pipeline_stages
    assert "skip_rag" in prepared.pipeline_stages
    build_tool_context.assert_not_called()
    maybe_extend_tool_context.assert_not_called()
    rag_context_service.build_context.assert_not_called()


def test_utility_time_uses_direct_answer_and_skips_rag_and_tools():
    session = MagicMock()
    session.id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    build_tool_context = MagicMock()
    maybe_extend_tool_context = MagicMock()

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    prepared = service.prepare(
        message="que horas são?",
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
    assert "Brasília" in prepared.direct_answer
    assert prepared.skip_rag is True
    assert "utility_direct" in prepared.pipeline_stages
    assert "skip_rag" in prepared.pipeline_stages
    build_tool_context.assert_not_called()
    maybe_extend_tool_context.assert_not_called()
    rag_context_service.build_context.assert_not_called()
