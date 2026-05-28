#!/usr/bin/env python3
"""Testa sequências operacionais multi-turn (estoque, filial, completo, lista)."""

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


def _tool_rows(prepared) -> list[dict]:
    rows = []

    for call in prepared.tool_calls or []:
        if call.get("name") != "execute_external_action":
            continue

        args = call.get("arguments") or {}
        rows.append(
            {
                "actionId": str(args.get("actionId") or ""),
                "parameters": dict(args.get("parameters") or {}),
                "reason": str(call.get("reason") or "")[:100],
            }
        )

    return rows


def _append_history(history: list, message: str, tools: list[dict]) -> None:
    history.append({"role": "user", "content": message})
    tool_calls = []

    for item in tools:
        code = (item.get("parameters") or {}).get("code", "")
        action_id = str(item.get("actionId") or "").lower()
        segment = "stock"

        if "summary" in action_id:
            segment = "summary"
        elif "purchases" in action_id:
            segment = "purchases"

        path = f"/products/{code}/{segment}" if code else ""

        tool_calls.append(
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": path,
                    "actionId": item.get("actionId"),
                    "responsePreview": f"Produto {code}",
                },
            }
        )

    history.append(
        {
            "role": "assistant",
            "content": "Resposta operacional.",
            "metadata": {"toolCalls": tool_calls},
        }
    )


def run_scenario(
    prep: ChatTurnPreparationService,
    tool_svc,
    session,
    workspace,
    steps: list[tuple[str, callable]],
) -> list[dict]:
    history: list = []
    results: list[dict] = []

    for message, checker in steps:
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

        prepared = prep.prepare(
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
            prepare_history=lambda items: ("", list(items[-8:])),
            history_keep=8,
            fast_path_enabled=True,
            fast_path_max_chars=48,
            resolve_user_identity_answer=lambda _message: None,
            resolve_capabilities_answer=lambda _message: None,
        )

        tools = _tool_rows(prepared)
        ok, detail = checker(tools)
        results.append(
            {
                "message": message,
                "ok": ok,
                "detail": detail,
                "tools": tools,
            }
        )

        if tools:
            _append_history(history, message, tools)
        else:
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": "sem tool"})

    return results


def main() -> int:
    app = create_application()
    failed = 0

    with app.app_context():
        sessions = PostgresChatSessionRepository().list_sessions_by_user(
            UUID("4ac305a6-0569-40b8-a918-b908cfeba169")
        )

        if not sessions:
            print("Sem sessão de teste.", file=sys.stderr)
            return 2

        session = sessions[0]
        workspace = make_chat_workspace_context_service().build_context(
            session=session,
            user_id=session.user_id,
        )
        prep = ChatTurnPreparationService(rag_context_service=make_rag_context_service())
        tool_svc = make_chat_tool_context_service()

        scenarios = {
            "estoque_filial_completo": [
                (
                    "estoque do produto 10080047",
                    lambda t: (
                        len(t) == 1
                        and "stock" in t[0]["actionId"]
                        and t[0]["parameters"].get("code") == "10080047"
                        and not t[0]["parameters"].get("branch"),
                        "estoque inicial sem filial",
                    ),
                ),
                (
                    "filtre filial 02",
                    lambda t: (
                        len(t) == 1
                        and "stock" in t[0]["actionId"]
                        and t[0]["parameters"].get("code") == "10080047"
                        and t[0]["parameters"].get("branch") == "02",
                        "refino filial 02",
                    ),
                ),
                (
                    "completo de novo",
                    lambda t: (
                        len(t) == 1
                        and "stock" in t[0]["actionId"]
                        and t[0]["parameters"].get("code") == "10080047"
                        and not t[0]["parameters"].get("branch"),
                        "estoque completo sem branch",
                    ),
                ),
                (
                    "estoque completo",
                    lambda t: (
                        len(t) == 1
                        and "stock" in t[0]["actionId"]
                        and not t[0]["parameters"].get("branch"),
                        "estoque completo",
                    ),
                ),
            ],
            "lista_dois_produtos_filial": [
                (
                    "estoque dos produtos 10080047 e 10080055",
                    lambda t: (
                        len(t) == 2
                        and {row["parameters"].get("code") for row in t}
                        == {"10080047", "10080055"},
                        "dois estoques",
                    ),
                ),
                (
                    "filtre filial 01",
                    lambda t: (
                        len(t) >= 1
                        and all(row["parameters"].get("branch") == "01" for row in t)
                        and all("stock" in row["actionId"] for row in t),
                        "filial 01 em todos",
                    ),
                ),
                (
                    "mostre completo",
                    lambda t: (
                        len(t) >= 1
                        and all(not row["parameters"].get("branch") for row in t),
                        "sem filial após completo",
                    ),
                ),
            ],
            "contexto_sem_codigo_apos_lista": [
                (
                    "resumo dos produtos 10080047 e 10080055",
                    lambda t: (
                        len(t) == 2 and "summary" in t[0]["actionId"],
                        "dois resumos",
                    ),
                ),
                (
                    "estoque do produto",
                    lambda t: (
                        len(t) == 1
                        and t[0]["parameters"].get("code") == "10080055",
                        "último produto da lista",
                    ),
                ),
            ],
        }

        report: dict[str, list] = {}

        for name, steps in scenarios.items():
            report[name] = run_scenario(prep, tool_svc, session, workspace, steps)

            for row in report[name]:
                if not row["ok"]:
                    failed += 1

        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"\n{sum(1 for s in report.values() for r in s if r['ok'])}/{sum(len(s) for s in report.values())} passos OK")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
