#!/usr/bin/env python3
"""Smoke: melhorias GPT_instructions + SQL operacional + visibilidade de fontes.

Valida preparação de turno (ChatTurnPreparationService) com agente minha-delpi-chat.

Uso:
  PYTHONPATH=/app python scripts/smoke_gpt_instructions_improvements.py [user_id] [session_id]
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
from app.domain.services.chat_source_visibility_service import filter_client_visible_sources
from app.infrastructure.persistence.postgres_chat_session_repository import (
    PostgresChatSessionRepository,
)

DEFAULT_USER = "4ac305a6-0569-40b8-a918-b908cfeba169"

# (mensagem, expectativas, rótulo)
QUESTIONS: list[tuple[str, dict, str]] = [
    (
        "quais produtos serão produzidos hoje?",
        {
            "skip_rag": True,
            "operational_optimize": True,
            "max_tool_calls": 1,
            "action_must_not_contain": ["search_products"],
            "action_contains": "sql",
        },
        "#G1 produção hoje → fast path SQL, sem search",
    ),
    (
        "me traga a programação de produção de hoje",
        {
            "skip_rag": True,
            "operational_optimize": True,
            "max_tool_calls": 1,
            "action_must_not_contain": ["search_products"],
            "action_contains": "sql",
        },
        "#G2 programação produção → fast path SQL",
    ),
    (
        "monte uma query que liste os produtos que vão ser produzidos hoje",
        {
            "skip_rag": True,
            "operational_optimize": True,
            "max_tool_calls": 0,
            "action_must_not_contain": ["search_products", "data/sql"],
            "direct_answer_contains": ["```sql", "SC2010"],
        },
        "#G3 elaborar SQL → resposta direta com query, sem LLM",
    ),
    (
        "estoque do produto 10080047",
        {
            "skip_rag": True,
            "operational_optimize": True,
            "max_tool_calls": 1,
            "action_contains": "stock",
        },
        "#G4 regressão estoque REST (fast path)",
    ),
    (
        "busque parafuso m8",
        {
            "skip_rag": True,
            "max_tool_calls": 1,
            "action_contains": "search",
        },
        "#G5 regressão busca catálogo (não confundir com SQL produção)",
    ),
    (
        "quais ordens de produção estão programadas para hoje?",
        {
            "skip_rag": True,
            "operational_optimize": True,
            "max_tool_calls": 1,
            "action_must_not_contain": ["search_products"],
            "action_contains": "sql",
        },
        "#G9 ordens de produção hoje → fast path SQL",
    ),
    (
        "liste a produção do dia na SC2010",
        {
            "skip_rag": True,
            "operational_optimize": True,
            "max_tool_calls": 1,
            "action_must_not_contain": ["search_products"],
            "action_contains": "sql",
        },
        "#G11 SC2010 explícito → SQL produção",
    ),
    (
        "monte o SQL da programação de produção de hoje sem executar",
        {
            "skip_rag": True,
            "operational_optimize": True,
            "max_tool_calls": 0,
            "action_must_not_contain": ["search_products"],
            "direct_answer_contains": ["```sql", "SC2010"],
        },
        "#G12 autoria SQL produção sem executar",
    ),
    (
        "qual rota da API DELPI retorna a ficha analyser completa?",
        {
            "rag_only": True,
            "rag_query": "product api analyser ficha completa rota endpoint",
            "rag_context_any": ["analyser", "/products/", "ficha", "product_api"],
            "rag_min_length": 200,
        },
        "#G6 RAG product_api ingerido",
    ),
    (
        "como listar tabelas do dicionário de dados protheus na API?",
        {
            "rag_only": True,
            "rag_query": "system api tabelas dicionario protheus sx2 colunas",
            "rag_context_any": ["system", "sx2", "tabelas", "/system/"],
            "rag_min_length": 150,
        },
        "#G7 RAG system_api ingerido",
    ),
    (
        "quais campos usar no POST /data/sql para consulta de produção?",
        {
            "rag_only": True,
            "rag_query": "data sql api SC2010 produção campos payload",
            "rag_context_any": ["consulta", "producao", "produção", "campo", "payload", "sc2010"],
            "rag_min_length": 150,
        },
        "#G13 RAG data_sql_api_instructions",
    ),
    (
        "quais regras de validação de desenho técnico existem?",
        {
            "rag_only": True,
            "rag_query": "drawing validation rules desenho conformidade",
            "rag_context_any": ["drawing", "validation", "desenho", "conformidade"],
            "rag_min_length": 100,
        },
        "#G14 RAG drawing/validation agente",
    ),
    (
        "como descrever um terminal?",
        {
            "skip_rag": False,
            "operational_optimize": False,
            "max_tool_calls": 0,
            "action_must_not_contain": ["search_products", "search"],
            "rag_min_length": 80,
            "rag_context_any": ["1008", "terminal", "normas", "descri"],
        },
        "#N1 normas terminais → RAG global, sem search",
    ),
    (
        "normas técnicas DELPI para terminais pino",
        {
            "skip_rag": False,
            "operational_optimize": False,
            "max_tool_calls": 0,
            "action_must_not_contain": ["search"],
            "rag_min_length": 80,
            "rag_context_any": ["1008", "pino", "terminal", "normas"],
        },
        "#N3 normas terminais pino",
    ),
    (
        "como descrever um cabo PP?",
        {
            "skip_rag": False,
            "operational_optimize": False,
            "max_tool_calls": 0,
            "action_must_not_contain": ["search"],
            "rag_min_length": 80,
            "rag_context_any": ["cabo", "1001", "1005", "normas", "pp"],
        },
        "#N5 normas cabos PP",
    ),
    (
        "qual a descrição do produto 10080047",
        {
            "skip_rag": True,
            "operational_optimize": True,
            "max_tool_calls": 1,
            "action_must_not_contain": ["search_products"],
        },
        "#N4 regressão descrição cadastral (REST, não Normas)",
    ),
    (
        "busque terminal m8",
        {
            "skip_rag": True,
            "max_tool_calls": 1,
            "action_contains": "search",
        },
        "#X3 busca catálogo terminal (não Normas)",
    ),
]


def _check(condition: bool, label: str, errors: list[str]) -> None:
    if not condition:
        errors.append(label)


def main() -> int:
    user_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER
    session_id = sys.argv[2] if len(sys.argv) > 2 else None

    app = create_application()
    results: list[dict] = []
    failed = 0

    with app.app_context():
        chat_repo = PostgresChatSessionRepository()
        workspace_svc = make_chat_workspace_context_service()
        tool_svc = make_chat_tool_context_service()
        prep_svc = ChatTurnPreparationService(rag_context_service=make_rag_context_service())

        if not session_id:
            sessions = chat_repo.list_sessions_by_user(UUID(user_id))
            if not sessions:
                print("Nenhuma sessão; passe user_id e session_id.", file=sys.stderr)
                return 2
            session = sessions[0]
            session_id = str(session.id)
            print(f"Sessão: {session_id} (agent_key={session.agent_key})\n", file=sys.stderr)
        else:
            session = chat_repo.get_session_by_id(UUID(session_id))
            if not session:
                print("Sessão não encontrada.", file=sys.stderr)
                return 2

        workspace = workspace_svc.build_context(session=session, user_id=UUID(user_id))

        if workspace.get("agentKey") != "minha-delpi-chat":
            print(
                f"Aviso: sessão usa agent_key={workspace.get('agentKey')!r}, "
                "esperado minha-delpi-chat para RAG do agente.",
                file=sys.stderr,
            )

        for message, expectations, label in QUESTIONS:
            errors: list[str] = []

            if expectations.get("rag_only"):
                from app.application.services.rag_context_service import RagContextService
                from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
                from app.composition.chat_composer import make_embedding_gateway
                from app.infrastructure.persistence.postgres_knowledge_repository import (
                    PostgresKnowledgeRepository,
                )

                rag_svc = RagContextService(
                    SearchKnowledgeUseCase(
                        PostgresKnowledgeRepository(),
                        make_embedding_gateway(),
                    )
                )
                rag_query = expectations.get("rag_query") or message
                rag_result = rag_svc.build_context(
                    rag_query,
                    filters={
                        "user_id": user_id,
                        "agent_key": workspace.get("agentKey") or "minha-delpi-chat",
                        "include_global": True,
                    },
                    min_score=0.2,
                )
                rag_context = (rag_result.get("context") or "").lower()
                rag_min = expectations.get("rag_min_length")
                if rag_min is not None:
                    _check(
                        len(rag_result.get("context") or "") >= rag_min,
                        f"rag context >= {rag_min} chars (foi {len(rag_result.get('context') or '')})",
                        errors,
                    )
                rag_any = expectations.get("rag_context_any")
                if rag_any:
                    _check(
                        any(term.lower() in rag_context for term in rag_any),
                        f"rag context contém um de {rag_any}",
                        errors,
                    )
                _check(
                    len(rag_result.get("sources") or []) == 0,
                    "fontes agente ocultas na resposta cliente",
                    errors,
                )
                ok = not errors
                if not ok:
                    failed += 1
                    print(f"FAIL {label}", file=sys.stderr)
                    print(f"  pergunta: {message}", file=sys.stderr)
                    for err in errors:
                        print(f"  - {err}", file=sys.stderr)
                results.append(
                    {
                        "label": label,
                        "message": message,
                        "ok": ok,
                        "errors": errors,
                        "ragOnly": True,
                        "ragContextLength": len(rag_result.get("context") or ""),
                        "clientSources": len(rag_result.get("sources") or []),
                    }
                )
                continue

            if "synthetic_history" in expectations:
                history_for_turn = expectations["synthetic_history"]
            else:
                history_for_turn = []

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
                    previous_messages=kwargs.get("previous_messages") or history_for_turn,
                    max_external_action_calls=kwargs.get("max_external_action_calls"),
                )

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
                maybe_extend_tool_context=lambda **kw: kw["tool_context"],
                prepare_history=lambda h: ("", list(h[-6:])),
                history_keep=6,
                fast_path_enabled=True,
                fast_path_max_chars=120,
                resolve_user_identity_answer=lambda _m: None,
                resolve_capabilities_answer=lambda _m: None,
            )

            tool_calls = prepared.tool_calls or []
            action_ids = [
                str((call.get("arguments") or {}).get("actionId") or "")
                for call in tool_calls
                if call.get("name") == "execute_external_action"
            ]
            rag_context = (prepared.rag.get("context") or "").lower()
            raw_sources = prepared.sources or []
            visible_sources = filter_client_visible_sources(raw_sources)

            if expectations.get("skip_rag") is not None:
                _check(
                    prepared.skip_rag is expectations["skip_rag"],
                    f"skip_rag={expectations['skip_rag']} (foi {prepared.skip_rag})",
                    errors,
                )

            if expectations.get("operational_optimize") is not None:
                _check(
                    prepared.operational_optimize is expectations["operational_optimize"],
                    f"operational_optimize={expectations['operational_optimize']} "
                    f"(foi {prepared.operational_optimize})",
                    errors,
                )

            max_tools = expectations.get("max_tool_calls")
            if max_tools is not None:
                _check(
                    len(tool_calls) <= max_tools,
                    f"tool_calls <= {max_tools} (foi {len(tool_calls)}: {action_ids})",
                    errors,
                )

            if "action_contains" in expectations:
                needle = expectations["action_contains"].lower()
                _check(
                    any(needle in aid.lower() for aid in action_ids),
                    f"actionId contém «{needle}» (foi {action_ids})",
                    errors,
                )
            elif expectations.get("max_tool_calls") == 1 and not expectations.get("action_contains"):
                _check(
                    len(action_ids) >= 1,
                    f"esperava ao menos 1 action (foi {action_ids})",
                    errors,
                )

            for forbidden in expectations.get("action_must_not_contain") or []:
                needle = forbidden.lower()
                _check(
                    not any(needle in aid.lower() for aid in action_ids),
                    f"actionId NÃO deve conter «{forbidden}» (foi {action_ids})",
                    errors,
                )

            rag_min = expectations.get("rag_min_length")
            if rag_min is not None:
                actual_len = len(prepared.rag.get("context") or "")
                _check(
                    actual_len >= rag_min,
                    f"rag context >= {rag_min} chars (foi {actual_len})",
                    errors,
                )

            rag_any = expectations.get("rag_context_any")
            if rag_any:
                _check(
                    any(term.lower() in rag_context for term in rag_any),
                    f"rag context contém um de {rag_any}",
                    errors,
                )

            direct_any = expectations.get("direct_answer_contains")
            if direct_any:
                direct_text = (prepared.direct_answer or "").lower()
                _check(
                    all(term.lower() in direct_text for term in direct_any),
                    f"direct_answer contém {direct_any} (preview: {(prepared.direct_answer or '')[:120]})",
                    errors,
                )

            if expectations.get("agent_sources_hidden"):
                agent_scopes = [
                    s.get("scope")
                    for s in raw_sources
                    if isinstance(s, dict)
                ]
                _check(
                    not visible_sources and any(scope == "agent_source" for scope in agent_scopes)
                    or all(s.get("scope") != "agent_source" for s in visible_sources if isinstance(s, dict)),
                    "fontes agent_source ocultas do cliente",
                    errors,
                )

            ok = not errors
            if not ok:
                failed += 1
                print(f"FAIL {label}", file=sys.stderr)
                print(f"  pergunta: {message}", file=sys.stderr)
                for err in errors:
                    print(f"  - {err}", file=sys.stderr)

            results.append(
                {
                    "label": label,
                    "message": message,
                    "ok": ok,
                    "errors": errors,
                    "skipRag": prepared.skip_rag,
                    "operationalOptimize": prepared.operational_optimize,
                    "toolCalls": len(tool_calls),
                    "actionIds": action_ids,
                    "ragContextLength": len(prepared.rag.get("context") or ""),
                    "rawSourceCount": len(raw_sources),
                    "visibleSourceCount": len(visible_sources),
                }
            )

        # Caso dedicado: visibilidade com RAG que retorna agent_source no contexto interno
        visibility_errors: list[str] = []
        from app.application.services.rag_context_service import RagContextService
        from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
        from app.composition.chat_composer import make_embedding_gateway
        from app.infrastructure.persistence.postgres_knowledge_repository import (
            PostgresKnowledgeRepository,
        )

        rag_svc = RagContextService(
            SearchKnowledgeUseCase(PostgresKnowledgeRepository(), make_embedding_gateway())
        )
        vis_rag = rag_svc.build_context(
            "ordens de produção SC2010",
            filters={
                "user_id": user_id,
                "agent_key": "minha-delpi-chat",
                "include_global": True,
            },
            min_score=0.2,
        )
        _check(len(vis_rag.get("context") or "") > 100, "RAG interno preenchido", visibility_errors)
        _check(
            len(vis_rag.get("sources") or []) == 0,
            "sources cliente vazias (agent_source oculto)",
            visibility_errors,
        )
        vis_ok = not visibility_errors
        if not vis_ok:
            failed += 1
            print("FAIL #G8 visibilidade fontes agente", file=sys.stderr)
            for err in visibility_errors:
                print(f"  - {err}", file=sys.stderr)

        results.append(
            {
                "label": "#G8 visibilidade agent_source",
                "ok": vis_ok,
                "errors": visibility_errors,
                "ragContextLength": len(vis_rag.get("context") or ""),
                "clientSources": len(vis_rag.get("sources") or []),
            }
        )

    print(json.dumps({"failed": failed, "total": len(results), "results": results}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
