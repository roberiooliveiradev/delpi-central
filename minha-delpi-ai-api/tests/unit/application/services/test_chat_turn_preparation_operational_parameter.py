"""Consultas operacionais sem parâmetro obrigatório: resposta direta, sem tools."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)


def test_stock_without_code_skips_tools_and_returns_direct_answer():
    session = MagicMock()
    session.id = uuid4()
    user_id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    build_tool_context = MagicMock(
        return_value={
            "context": "should-not-run",
            "toolCalls": [{"name": "execute_external_action"}],
            "nativeToolCalling": {},
        }
    )

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    prepared = service.prepare(
        message="estoque do produto",
        request=request,
        session=session,
        user_id=user_id,
        workspace_context={
            "skills": {"companyKnowledge": True},
            "allowedActionIds": ["commercial-rol", "stock-action"],
            "capabilities": {"actions": True},
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

    build_tool_context.assert_not_called()
    assert prepared.direct_answer
    assert "agente" in prepared.direct_answer.lower()
    assert prepared.tool_calls == []
    assert prepared.skip_rag is True
    rag_context_service.build_context.assert_not_called()
