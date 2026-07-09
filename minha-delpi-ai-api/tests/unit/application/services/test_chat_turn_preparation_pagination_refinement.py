"""Follow-up de paginação (ex.: aumente para 50 linhas) mantém fast path e skip RAG."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)

_PARENTS_HISTORY = [
    {"role": "user", "content": "onde é usado o 10080022"},
    {
        "role": "assistant",
        "content": "Produtos pai (onde é usado)",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "parents-action",
                        "parameters": {
                            "code": "10080022",
                            "page": 1,
                            "page_size": 25,
                        },
                    },
                    "metadata": {
                        "ok": True,
                        "path": "/products/10080022/parents",
                        "actionId": "parents-action",
                        "dataCoverageNotice": {
                            "kind": "pagination",
                            "message": "Produtos pai parcial: página 1 de 3.",
                        },
                    },
                }
            ]
        },
    },
]


def test_parents_page_size_refinement_skips_rag_and_keeps_operational_mode():
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
                        "actionId": "parents-action",
                        "parameters": {
                            "code": "10080022",
                            "page": 1,
                            "page_size": 50,
                        },
                    },
                    "metadata": {
                        "ok": True,
                        "path": "/products/10080022/parents",
                        "actionId": "parents-action",
                        "preferredFormat": "tree",
                        "treePresentation": {
                            "type": "tree",
                            "title": "Onde é usado o produto 10080022",
                            "root": {
                                "id": "10080022",
                                "label": "10080022",
                                "children": [],
                            },
                        },
                        "tablePresentation": {
                            "type": "table",
                            "title": "Produtos pai (onde é usado)",
                            "columns": [{"key": "code", "label": "Código"}],
                            "rows": [{"code": "23-011"}] * 50,
                        },
                        "dataCoverageNotice": {
                            "kind": "pagination",
                            "message": "Produtos pai parcial: página 1 de 9 (50 de 419 registro(s)).",
                        },
                    },
                }
            ],
            "nativeToolCalling": {},
        }
    )

    service = ChatTurnPreparationService(rag_context_service=rag_context_service)

    prepared = service.prepare(
        message="aumente para 50 linhas",
        request=request,
        session=session,
        user_id=user_id,
        workspace_context={
            "userActivatedAgent": True,
            "actionsEnabled": True,
            "skills": {"companyKnowledge": True},
            "allowedActionIds": ["parents-action"],
            "capabilities": {"actions": True},
        },
        attachments=[],
        previous_messages=_PARENTS_HISTORY,
        history_source=_PARENTS_HISTORY,
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
    assert "skip_rag" in prepared.pipeline_stages
    assert "tools" in prepared.pipeline_stages
    rag_context_service.build_context.assert_not_called()

    params = (prepared.tool_calls[0].get("arguments") or {}).get("parameters") or {}
    assert params.get("code") == "10080022"
    assert params.get("page_size") == 50

    notice = prepared.tool_calls[0]["metadata"]["dataCoverageNotice"]
    assert notice["kind"] == "pagination"
    assert "50" in notice["message"]
