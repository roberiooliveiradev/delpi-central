"""Follow-up de estoque (ex.: filtrar filial) mantém fast path operacional e skip RAG."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)

_STOCK_HISTORY = [
    {"role": "user", "content": "estoque do produto 10080022"},
    {
        "role": "assistant",
        "content": "Estoque do produto 10080022",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": "/products/10080022/stock",
                        "actionId": "get_product_stock",
                    },
                }
            ]
        },
    },
]


def test_stock_branch_refinement_skips_rag_and_keeps_operational_mode():
    session = MagicMock()
    session.id = uuid4()
    user_id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    build_tool_context = MagicMock(
        return_value={
            "context": "",
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "stock-action",
                        "parameters": {"code": "10080022", "branch": "02"},
                    },
                }
            ],
            "nativeToolCalling": {},
        }
    )

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    prepared = service.prepare(
        message="filtre filial 02",
        request=request,
        session=session,
        user_id=user_id,
        workspace_context={
            "skills": {"companyKnowledge": True},
            "allowedActionIds": ["stock-action"],
            "capabilities": {"actions": True},
        },
        attachments=[],
        previous_messages=_STOCK_HISTORY,
        history_source=_STOCK_HISTORY,
        build_tool_context=build_tool_context,
        maybe_extend_tool_context=lambda **kwargs: kwargs["tool_context"],
        prepare_history=lambda history: ("", list(history)),
        history_keep=12,
        fast_path_enabled=True,
        fast_path_max_chars=30,
        resolve_user_identity_answer=lambda msg: None,
        resolve_capabilities_answer=lambda msg: None,
    )

    build_tool_context.assert_called_once()
    assert prepared.operational_optimize is True
    assert prepared.skip_rag is True
    rag_context_service.build_context.assert_not_called()
    params = (prepared.tool_calls[0].get("arguments") or {}).get("parameters") or {}
    assert params.get("branch") == "02"
