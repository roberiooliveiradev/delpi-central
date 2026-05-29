#!/usr/bin/env python3
"""Smoke: perguntas operacionais reais — valida preparação do turno (sem LLM lento).

Espelha o checklist em docs/testing/smoke-operacional-manual.md.
Execute: PYTHONPATH=/app python scripts/smoke_operational_questions.py
"""

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

_STOCK_VALUE_HISTORY = [
    {"role": "user", "content": "qual o valor total de estoque da empresa"},
    {
        "role": "assistant",
        "content": "Valor Total de Estoque",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": "/supplies/stock-value",
                        "actionId": "get_supplies_stock_value",
                    },
                }
            ]
        },
    },
]

_CPV_HISTORY = [
    {"role": "user", "content": "qual o cpv"},
    {
        "role": "assistant",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {"ok": True, "path": "/supplies/cpv"},
                }
            ]
        },
    },
]

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
                        "actionId": "parents",
                        "parameters": {
                            "code": "10080022",
                            "page": 1,
                            "page_size": 25,
                        },
                    },
                    "metadata": {
                        "ok": True,
                        "path": "/products/10080022/parents",
                        "actionId": "parents",
                        "dataCoverageNotice": {
                            "kind": "pagination",
                            "details": {
                                "pagination": {
                                    "page": 1,
                                    "pageSize": 25,
                                    "total": 419,
                                    "totalPages": 17,
                                }
                            },
                        },
                    },
                }
            ]
        },
    },
]

_TWO_PRODUCTS_HISTORY = [
    {"role": "user", "content": "resumo dos produtos 10080047 e 10080055"},
    {
        "role": "assistant",
        "content": "Produto 10080047: A\nProduto 10080055: B",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {"ok": True, "path": "/products/10080047/summary"},
                },
                {
                    "name": "execute_external_action",
                    "metadata": {"ok": True, "path": "/products/10080055/summary"},
                },
            ]
        },
    },
]

# (mensagem, expectativas, rótulo do checklist manual)
QUESTIONS: list[tuple[str, dict, str]] = [
    (
        "estoque do produto",
        {
            "synthetic_history": [],
            "direct_answer_contains": "código",
            "max_tool_calls": 0,
            "skip_rag": True,
        },
        "#1 estoque sem código",
    ),
    (
        "estouque do produto",
        {
            "synthetic_history": [],
            "direct_answer_contains": "código",
            "max_tool_calls": 0,
            "skip_rag": True,
        },
        "#2 typo estouque",
    ),
    (
        "estoque do produto 10080022",
        {
            "action_contains": "stock",
            "max_tool_calls": 1,
            "skip_rag": True,
        },
        "#3 estoque com código",
    ),
    (
        "quem te criou?",
        {
            "direct_answer_contains": "minha delpi",
            "skip_rag": True,
            "max_tool_calls": 0,
        },
        "#4 identidade assistente",
    ),
    (
        "olá",
        {
            "max_tool_calls": 0,
        },
        "#5 saudação",
    ),
    (
        "filtre filial 02",
        {
            "synthetic_history": _STOCK_HISTORY,
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "stock",
            "max_tool_calls": 1,
            "branch_param": "02",
        },
        "#6 refinamento estoque filial",
    ),
    (
        "filial 01",
        {
            "synthetic_history": _STOCK_VALUE_HISTORY,
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "stock",
            "max_tool_calls": 1,
            "branch_param": "01",
            "answer_must_not_contain": ["select ", "sql"],
        },
        "#6b KPI estoque empresa + filial curta",
    ),
    (
        "filtre filial 02",
        {
            "synthetic_history": _CPV_HISTORY,
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "cpv",
            "max_tool_calls": 1,
            "branch_param": "02",
        },
        "#34 CPV + filial",
    ),
    (
        "completo de novo",
        {
            "synthetic_history": _STOCK_HISTORY
            + [{"role": "user", "content": "filtre filial 02"}],
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "stock",
            "max_tool_calls": 1,
        },
        "#12 reset estoque completo",
    ),
    (
        "estoque do produto",
        {
            "synthetic_history": _TWO_PRODUCTS_HISTORY,
            "action_contains": "stock",
            "max_tool_calls": 1,
        },
        "#18 estoque último produto citado",
    ),
    (
        "qual o valor total de estoque da empresa",
        {
            "action_contains": "stock",
            "max_tool_calls": 1,
        },
        "#24 KPI estoque empresa",
    ),
    (
        "ficha completa do produto 10080047",
        {
            "action_contains": "analyser",
            "max_tool_calls": 1,
            "skip_rag": True,
        },
        "#23 analyser ficha completa",
    ),
    (
        "resumo do produto 10080047",
        {
            "action_contains": "summary",
            "max_tool_calls": 1,
        },
        "#22 summary não analyser",
    ),
    (
        "cpv de 01/04/2026 a 30/04/2026",
        {
            "action_contains": "cpv",
            "max_tool_calls": 1,
            "date_start": "01-04-2026",
            "date_end": "30-04-2026",
        },
        "#32 CPV com datas",
    ),
    (
        "aumente para 50 linhas",
        {
            "synthetic_history": _PARENTS_HISTORY,
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "parent",
            "max_tool_calls": 1,
            "page_size_param": 50,
        },
        "#49 paginação page_size",
    ),
    (
        "proxima pagina",
        {
            "synthetic_history": _PARENTS_HISTORY,
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "parent",
            "max_tool_calls": 1,
            "page_param": 2,
        },
        "#50 próxima página",
    ),
    (
        "pagina anterior",
        {
            "synthetic_history": _PARENTS_HISTORY
            + [{"role": "user", "content": "proxima pagina"}],
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "parent",
            "max_tool_calls": 1,
            "page_param": 1,
        },
        "#51 página anterior",
    ),
    (
        "onde é usado o 10080022",
        {
            "action_contains": "parent",
            "max_tool_calls": 1,
        },
        "#46 parents inicial",
    ),
    (
        "estrutura do produto 90260088",
        {
            "action_contains": "structure",
            "max_tool_calls": 1,
        },
        "#31 estrutura (não comparação)",
    ),
    (
        "próxima página",
        {
            "synthetic_history": _PARENTS_HISTORY,
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "parent",
            "max_tool_calls": 1,
            "page_param": 2,
        },
        "#50 typo acento próxima página",
    ),
    (
        "aumente pra 50 linhas",
        {
            "synthetic_history": _PARENTS_HISTORY,
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "parent",
            "max_tool_calls": 1,
            "page_size_param": 50,
        },
        "#49 typo aumente pra",
    ),
    (
        "filail 01",
        {
            "synthetic_history": _STOCK_VALUE_HISTORY,
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "stock",
            "max_tool_calls": 1,
            "branch_param": "01",
        },
        "#6b typo filail",
    ),
    (
        "filtre filial 02 armazém 01",
        {
            "synthetic_history": _STOCK_HISTORY,
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "stock",
            "max_tool_calls": 1,
            "branch_param": "02",
            "warehouse_param": "01",
        },
        "#8 filial + armazém combinados",
    ),
    (
        "estoque completo",
        {
            "synthetic_history": _STOCK_HISTORY
            + [{"role": "user", "content": "filtre filial 02"}],
            "skip_rag": True,
            "operational_optimize": True,
            "action_contains": "stock",
            "max_tool_calls": 1,
        },
        "#13 estoque completo reset",
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

        for message, expectations, label in QUESTIONS:
            if "synthetic_history" in expectations:
                history_for_turn = expectations["synthetic_history"]
            else:
                history_for_turn = previous

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
                previous_messages=history_for_turn,
                history_source=history_for_turn,
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
            answer_lower = (prepared.direct_answer or "").lower()

            if "direct_answer_contains" in expectations:
                needle = expectations["direct_answer_contains"].lower()
                _check(needle in answer_lower, f"direct_answer deve conter «{needle}»", errors)

            for forbidden in expectations.get("answer_must_not_contain") or []:
                _check(
                    forbidden.lower() not in answer_lower,
                    f"direct_answer não deve conter «{forbidden}»",
                    errors,
                )

            if expectations.get("skip_rag") is not None:
                _check(
                    prepared.skip_rag is expectations["skip_rag"],
                    f"skip_rag={expectations['skip_rag']}",
                    errors,
                )

            if expectations.get("operational_optimize") is not None:
                _check(
                    prepared.operational_optimize is expectations["operational_optimize"],
                    f"operational_optimize={expectations['operational_optimize']}",
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
                needle = expectations["action_contains"].lower()
                _check(
                    any(needle in aid.lower() for aid in action_ids),
                    f"actionId deve conter «{needle}» (foi {action_ids})",
                    errors,
                )

            external_calls = [
                call for call in tool_calls if call.get("name") == "execute_external_action"
            ]
            params = (
                (external_calls[0].get("arguments") or {}).get("parameters") or {}
                if external_calls
                else {}
            )

            if "branch_param" in expectations:
                branch = expectations["branch_param"]
                _check(
                    str(params.get("branch") or "") == branch,
                    f"parameters.branch={branch} (foi {params.get('branch')})",
                    errors,
                )

            if "warehouse_param" in expectations:
                warehouse = expectations["warehouse_param"]
                actual_wh = (
                    params.get("warehouse")
                    or params.get("warehouse_code")
                    or params.get("armazem")
                    or params.get("location")
                    or params.get("local")
                )
                _check(
                    str(actual_wh or "") == warehouse,
                    f"parameters.warehouse={warehouse} (foi {actual_wh})",
                    errors,
                )

            if "page_size_param" in expectations:
                expected = expectations["page_size_param"]
                actual = params.get("page_size") or params.get("pageSize")
                _check(
                    int(actual or 0) == expected,
                    f"parameters.page_size={expected} (foi {actual})",
                    errors,
                )

            if "page_param" in expectations:
                expected = expectations["page_param"]
                actual = params.get("page")
                _check(
                    int(actual or 0) == expected,
                    f"parameters.page={expected} (foi {actual})",
                    errors,
                )

            if "date_start" in expectations:
                _check(
                    str(params.get("start_date") or "") == expectations["date_start"],
                    f"start_date={expectations['date_start']}",
                    errors,
                )

            if "date_end" in expectations:
                _check(
                    str(params.get("end_date") or "") == expectations["date_end"],
                    f"end_date={expectations['date_end']}",
                    errors,
                )

            _check(len(agentic_calls) == 0, "sem chamadas do loop agentic", errors)

            ok = not errors
            if not ok:
                failed += 1
                print(f"FAIL {label}: {message}", file=sys.stderr)
                for err in errors:
                    print(f"  - {err}", file=sys.stderr)

            results.append(
                {
                    "label": label,
                    "message": message,
                    "ok": ok,
                    "errors": errors,
                    "directAnswerPreview": (prepared.direct_answer or "")[:200],
                    "skipRag": prepared.skip_rag,
                    "operationalOptimize": prepared.operational_optimize,
                    "toolCallCount": len(tool_calls),
                    "actionIds": action_ids,
                    "parameters": params,
                    "agenticCallCount": len(agentic_calls),
                }
            )

    sys.stdout.write(json.dumps(results, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    print(f"\n{len(results) - failed}/{len(results)} OK", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
