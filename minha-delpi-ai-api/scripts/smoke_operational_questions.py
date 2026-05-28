#!/usr/bin/env python3
"""Smoke: perguntas operacionais reais — valida preparação do turno (sem LLM lento)."""

from __future__ import annotations

import json
import sys
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)
from app.composition.chat_composer import (
    make_chat_tool_context_service,
    make_chat_workspace_context_service,
    make_rag_context_service,
)
from app.composition.root_composer import create_application
from app.infrastructure.persistence.postgres_chat_session_repository import (
    PostgresChatSessionRepository,
)


QUESTIONS: list[tuple[str, dict]] = [
    (
        "estoque do produto",
        {
            "direct_answer_contains": "código",
            "max_tool_calls": 0,
            "skip_rag": True,
        },
    ),
    (
        "estouque do produto",
        {
            "direct_answer_contains": "código",
            "max_tool_calls": 0,
        },
    ),
    (
        "estoque do produto 10080099",
        {
            "action_contains": "product_stock",
            "max_tool_calls": 1,
        },
    ),
    (
        "quem te criou?",
        {
            "direct_answer_contains": "minha delpi",
            "skip_rag": True,
            "max_tool_calls": 0,
        },
    ),
    (
        "olá",
        {
            "max_tool_calls": 0,
        },
    ),
]


def _check(condition: bool, label: str, errors: list[str]) -> None:
    if not condition:
        errors.append(label)


def main() -> int:
    user_id = sys.argv[1] if len(sys.argv) > 1 else None
    session_id = sys.argv[2] if len(sys.argv) > 2 else None

    app = create_application()
    results: list[dict] = []
    failed = 0

    with app.app_context():
        chat_repo = PostgresChatSessionRepository()
        workspace_svc = make_chat_workspace_context_service()
        tool_svc = make_chat_tool_context_service()
        prep_svc = ChatTurnPreparationService(
            rag_context_service=make_rag_context_service(),
        )

        if not user_id or not session_id:
            sessions = chat_repo.list_sessions_by_user(
                UUID("4ac305a6-0569-40b8-a918-b908cfeba169")
            )
            if not sessions:
                print("Nenhuma sessão encontrada; passe user_id e session_id.", file=sys.stderr)
                return 2
            session = sessions[0]
            user_id = str(session.user_id)
            session_id = str(session.id)
            print(f"Usando sessão {session_id} (user {user_id})\n", file=sys.stderr)

        session = chat_repo.get_session_by_id(UUID(session_id))
        if not session:
            print("Sessão não encontrada.", file=sys.stderr)
            return 2

        workspace = workspace_svc.build_context(session=session, user_id=UUID(user_id))
        previous = chat_repo.list_messages_by_session(UUID(session_id))

        for message, expectations in QUESTIONS:
            request = SendChatMessageRequest(
                user_id=user_id,
                session_id=session_id,
                message=message,
                access_token=None,
            )
            errors: list[str] = []

            def build_tool_context(req, **kwargs):
                return tool_svc.build_context(
                    user_id=req.user_id,
                    access_token=req.access_token or "",
                    message=message,
                    allowed_action_ids=kwargs.get("allowed_action_ids")
                    or workspace.get("allowedActionIds"),
                    actions_enabled=bool(workspace.get("actionsEnabled")),
                    fast_path=kwargs.get("fast_path", False),
                    previous_messages=kwargs.get("previous_messages") or [],
                    max_external_action_calls=kwargs.get("max_external_action_calls"),
                )

            def maybe_extend(**kwargs):
                return kwargs["tool_context"]

            prepared = prep_svc.prepare(
                message=message,
                request=request,
                session=session,
                user_id=UUID(user_id),
                workspace_context=workspace,
                attachments=[],
                previous_messages=previous,
                history_source=previous,
                build_tool_context=build_tool_context,
                maybe_extend_tool_context=maybe_extend,
                prepare_history=lambda h: ("", list(h[-6:])),
                history_keep=6,
                fast_path_enabled=True,
                fast_path_max_chars=30,
                resolve_user_identity_answer=lambda _m: None,
                resolve_capabilities_answer=lambda _m: None,
            )

            tool_calls = prepared.tool_calls or []
            action_ids = [
                str((call.get("arguments") or {}).get("actionId") or "")
                for call in tool_calls
                if call.get("name") == "execute_external_action"
            ]
            agentic_calls = [
                call
                for call in tool_calls
                if "Loop agentic" in str(call.get("reason") or "")
            ]

            if "direct_answer_contains" in expectations:
                needle = expectations["direct_answer_contains"].lower()
                answer = (prepared.direct_answer or "").lower()
                _check(needle in answer, f"direct_answer deve conter «{needle}»", errors)

            if expectations.get("skip_rag") is not None:
                _check(
                    prepared.skip_rag is expectations["skip_rag"],
                    f"skip_rag={expectations['skip_rag']}",
                    errors,
                )

            max_tools = expectations.get("max_tool_calls")
            if max_tools is not None:
                _check(
                    len(tool_calls) <= max_tools,
                    f"tool_calls <= {max_tools} (foi {len(tool_calls)})",
                    errors,
                )

            if "action_contains" in expectations:
                needle = expectations["action_contains"]
                _check(
                    any(needle in aid for aid in action_ids),
                    f"actionId deve conter «{needle}»",
                    errors,
                )

            _check(
                len(agentic_calls) == 0,
                "sem chamadas do loop agentic",
                errors,
            )

            ok = not errors
            if not ok:
                failed += 1

            results.append(
                {
                    "message": message,
                    "ok": ok,
                    "errors": errors,
                    "directAnswerPreview": (prepared.direct_answer or "")[:200],
                    "skipRag": prepared.skip_rag,
                    "toolCallCount": len(tool_calls),
                    "actionIds": action_ids,
                    "agenticCallCount": len(agentic_calls),
                }
            )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n{len(results) - failed}/{len(results)} OK", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
