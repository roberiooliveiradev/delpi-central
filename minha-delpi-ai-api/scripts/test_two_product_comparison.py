#!/usr/bin/env python3
"""Testa ficha/análise completa de dois produtos + comparação."""

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


def _append_history(history: list, message: str, tools: list[dict], preview: str = "") -> None:
    history.append({"role": "user", "content": message})
    tool_calls = []

    for item in tools:
        code = item.get("code") or ""
        action_id = str(item.get("actionId") or "").lower()
        segment = "analyser" if "analyser" in action_id else "structure"

        if "structure" in action_id:
            segment = "structure"
        elif "summary" in action_id:
            segment = "summary"

        humanized = {
            "titulo": f"Informações do produto {code}",
            "linhas": [
                f"Produto {code}: TERM. PINO RETO.",
                f"Tipo MP, unidade PC, grupo 1008.",
            ],
        }

        tool_calls.append(
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": f"/products/{code}/{segment}",
                    "actionId": item.get("actionId"),
                    "responsePreview": preview or humanized["linhas"][0],
                    "humanizedSummary": humanized,
                },
            }
        )

    history.append(
        {
            "role": "assistant",
            "content": preview or "Resposta.",
            "metadata": {"toolCalls": tool_calls},
        }
    )


def main() -> int:
    app = create_application()

    with app.app_context():
        sessions = PostgresChatSessionRepository().list_sessions_by_user(
            UUID("4ac305a6-0569-40b8-a918-b908cfeba169")
        )

        if not sessions:
            print("Sem sessão.", file=sys.stderr)
            return 2

        session = sessions[0]
        workspace = make_chat_workspace_context_service().build_context(
            session=session,
            user_id=session.user_id,
        )
        prep = ChatTurnPreparationService(rag_context_service=make_rag_context_service())
        tool_svc = make_chat_tool_context_service()
        history: list = []
        report: list[dict] = []

        def run_turn(message: str):
            user_id = str(session.user_id)
            session_id = str(session.id)
            request = SendChatMessageRequest(
                user_id=user_id,
                session_id=session_id,
                message=message,
                access_token=None,
            )

            def build_tool_context(req, **kwargs):
                return tool_svc.build_context(
                    user_id=req.user_id,
                    access_token="",
                    message=message,
                    allowed_action_ids=kwargs.get("allowed_action_ids")
                    or workspace.get("allowedActionIds"),
                    actions_enabled=bool(workspace.get("actionsEnabled")),
                    previous_messages=kwargs.get("previous_messages") or history,
                )

            return prep.prepare(
                message=message,
                request=request,
                session=session,
                user_id=session.user_id,
                workspace_context=workspace,
                attachments=[],
                previous_messages=history,
                history_source=history,
                build_tool_context=build_tool_context,
                maybe_extend_tool_context=lambda **kwargs: kwargs["tool_context"],
                prepare_history=lambda items: ("", list(items[-12:])),
                history_keep=12,
                fast_path_enabled=True,
                fast_path_max_chars=48,
                resolve_user_identity_answer=lambda _message: None,
                resolve_capabilities_answer=lambda _message: None,
            )

        msg1 = "traga a analise completa dos produtos 10080047 e 10080055"
        p1 = run_turn(msg1)
        tools1 = [
            {
                "actionId": str((c.get("arguments") or {}).get("actionId") or ""),
                "code": (c.get("arguments") or {}).get("parameters", {}).get("code"),
            }
            for c in p1.tool_calls or []
            if c.get("name") == "execute_external_action"
        ]
        report.append(
            {
                "step": 1,
                "message": msg1,
                "toolCount": len(tools1),
                "tools": tools1,
                "ok": len(tools1) == 2 and all("analyser" in t["actionId"] for t in tools1),
            }
        )
        _append_history(history, msg1, tools1)

        msg2 = "compare os dois produtos e traga insights"
        p2 = run_turn(msg2)
        report.append(
            {
                "step": 2,
                "message": msg2,
                "analysisMode": p2.analysis_mode,
                "directAnswer": bool(p2.direct_answer),
                "preview": (p2.direct_answer or "")[:300],
                "toolCount": len(p2.tool_calls or []),
                "ok": bool(p2.direct_answer)
                and (
                    "comparação" in (p2.direct_answer or "").lower()
                    or "comparacao" in (p2.direct_answer or "").lower()
                ),
            }
        )

        print(json.dumps(report, ensure_ascii=False, indent=2))
        failed = sum(1 for row in report if not row.get("ok"))

        return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
