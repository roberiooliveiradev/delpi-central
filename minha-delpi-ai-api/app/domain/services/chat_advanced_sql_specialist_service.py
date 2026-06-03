"""Orquestrador do Especialista SQL Avançado — Playbook §5–7."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Literal

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_sql_dialect_resolver_service import (
    ChatSqlDialectResolverService,
)
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_memory_workspace_service import (
    ChatSqlMemoryWorkspaceService,
)
from app.domain.services.chat_sql_performance_advisor_service import (
    ChatSqlPerformanceAdvisorService,
)
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)
from app.domain.services.chat_sql_review_service import ChatSqlReviewService
from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService
from app.infrastructure.content.content_service import ContentService

SqlSpecialistMode = Literal[
    "create",
    "review",
    "explain",
    "optimize",
    "execute",
    "schema_explore",
    "incremental_edit",
    "analyze_result",
    "visualize",
    "none",
]

_SQL_ACTIVATION_TERMS = (
    "sql",
    "consulta",
    "query",
    "select",
    "tabela",
    "coluna",
    "schema",
    "join",
    "agrup",
    "filtr",
    "orden",
    "ranking",
    "cte",
    "window",
    "executar consulta",
    "trazer dados",
    "otimiz",
    "explic",
    "revis",
)

_MODE_PATTERNS: tuple[tuple[SqlSpecialistMode, tuple[str, ...]], ...] = (
    (
        "review",
        (
            "revisa",
            "revise",
            "valida essa query",
            "valida esse sql",
            "esta correta",
            "está correta",
            "esta certa",
            "está certa",
            "tem erro",
            "aponta risco",
        ),
    ),
    (
        "explain",
        (
            "explique a query",
            "explique essa query",
            "explique o sql",
            "explique essa consulta",
            "o que faz essa query",
            "o que faz esse sql",
            "entenda essa query",
        ),
    ),
    (
        "optimize",
        (
            "otimiz",
            "melhorar performance",
            "query lenta",
            "consulta lenta",
            "demorad",
            "indice",
            "índice",
            "explain plan",
        ),
    ),
    (
        "schema_explore",
        (
            "quais tabelas",
            "qual tabela",
            "quais colunas",
            "mostre as colunas",
            "mostra as colunas",
            "schema da tabela",
            "schema completo",
            "relacion",
            "como relacionar",
            "procure coluna",
            "busque coluna",
        ),
    ),
    (
        "analyze_result",
        (
            "interprete o resultado",
            "interprete resultado",
            "analise o resultado",
            "analise resultado",
            "o que significa",
            "inferir resultado",
        ),
    ),
    (
        "visualize",
        (
            "gerar grafico",
            "gerar gráfico",
            "gere um grafico",
            "gere um gráfico",
            "gere grafico",
            "gere gráfico",
            "mostre em grafico",
            "mostre em gráfico",
            "visualiz",
            "chart",
        ),
    ),
)

_INCREMENTAL_EDIT_TERMS = (
    "consulta anterior",
    "query anterior",
    "sql anterior",
    "adicione a coluna",
    "adiciona a coluna",
    "remova a coluna",
    "remove a coluna",
    "agrup",
    "ordene",
    "filtre",
    "filtra ",
    "ajuste a query",
    "ajusta a query",
)

_PLANNER_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("compar", "periodo", "período", "mes anterior", "mês anterior", "ano anterior"), "use_cte_period_compare"),
    (("ranking", "top ", "maior", "menor", "por categoria"), "use_window_rank"),
    (("ultimo registro", "último registro", "mais recente por"), "use_row_number_dedup"),
    (("variacao", "variação", "percentual", "%"), "guard_division_by_zero"),
    (("deduplic", "duplicad", "unico", "único"), "use_row_number_dedup"),
    (("pivot", "cruzad", "matriz"), "use_pivot_or_conditional_agg"),
)


@lru_cache(maxsize=1)
def _interactivity_content() -> dict[str, Any]:
    return ContentService.load_json("assistant/interactivity")


class ChatAdvancedSqlSpecialistService:
    @classmethod
    def should_activate(
        cls,
        message: str | None,
        *,
        workspace_context: dict | None = None,
    ) -> bool:
        if not cls._sql_authoring_enabled(workspace_context):
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if ChatSqlSafetyService.contains_destructive_sql(message):
            return True

        if ChatSqlIntentService.is_authoring_request(message):
            return True

        if ChatSqlIntentService.should_auto_execute_sql(str(message or "")):
            return True

        if ChatSqlQueryRefinementService.is_sql_follow_up(
            str(message or ""),
            previous_messages=None,
        ):
            return True

        if ChatSqlPerformanceAdvisorService.extract_sql_block(message):
            return True

        return any(term in normalized for term in _SQL_ACTIVATION_TERMS)

    @classmethod
    def classify_mode(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> SqlSpecialistMode:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return "none"

        for mode, patterns in _MODE_PATTERNS:
            if mode in {"analyze_result", "visualize", "explain", "review", "optimize", "schema_explore"}:
                if any(pattern in normalized for pattern in patterns):
                    return mode

        if ChatSqlQueryRefinementService.is_sql_follow_up(
            str(message or ""),
            previous_messages=previous_messages,
        ):
            return "incremental_edit"

        if any(term in normalized for term in _INCREMENTAL_EDIT_TERMS):
            workspace = ChatSqlMemoryWorkspaceService.build_workspace(
                message=message,
                previous_messages=previous_messages,
            )

            if workspace.get("hasActiveQuery") or "anterior" in normalized:
                return "incremental_edit"

        if ChatSqlIntentService.should_auto_execute_sql(str(message or "")):
            return "execute"

        if ChatSqlPerformanceAdvisorService.extract_sql_block(message) and any(
            token in normalized for token in ("revisa", "valida", "corrig", "ajust")
        ):
            return "review"

        if ChatSqlPerformanceAdvisorService.extract_sql_block(message) and "explique" in normalized:
            return "explain"

        if ChatSqlIntentService.is_authoring_request(message):
            return "create"

        if any(term in normalized for term in _SQL_ACTIVATION_TERMS):
            return "create"

        return "none"

    @classmethod
    def build_pipeline_snapshot(
        cls,
        *,
        message: str | None,
        workspace_context: dict | None = None,
        previous_messages: list[Any] | None = None,
        tool_calls: list | None = None,
    ) -> dict[str, Any] | None:
        if not cls.should_activate(message, workspace_context=workspace_context):
            return None

        mode = cls.classify_mode(message, previous_messages=previous_messages)
        dialect = ChatSqlDialectResolverService.resolve(message, workspace_context=workspace_context)
        workspace = ChatSqlMemoryWorkspaceService.build_workspace(
            message=message,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
        )
        sql_text = workspace.get("currentSql") or ChatSqlPerformanceAdvisorService.extract_sql_block(
            message
        )
        blocked = ChatSqlSafetyService.contains_destructive_sql(message) or (
            bool(sql_text) and ChatSqlSafetyService.contains_destructive_sql(str(sql_text))
        )
        performance = (
            ChatSqlPerformanceAdvisorService.analyze(str(sql_text), dialect=str(dialect["dialect"]))
            if sql_text
            else ChatSqlPerformanceAdvisorService.analyze_message(
                message,
                dialect=str(dialect["dialect"]),
            )
        )

        from app.domain.services.chat_sql_schema_discovery_service import (
            ChatSqlSchemaDiscoveryService,
        )

        schema_discovery = ChatSqlSchemaDiscoveryService.build_schema_snapshot(
            message=message,
            tool_calls=tool_calls,
            current_sql=sql_text,
        )
        review = (
            ChatSqlReviewService.review(str(sql_text), dialect=str(dialect["dialect"]))
            if sql_text and mode in {"review", "optimize", "execute"}
            else None
        )

        from app.domain.services.chat_sql_result_analyzer_service import (
            ChatSqlResultAnalyzerService,
        )
        from app.domain.services.chat_sql_visualization_advisor_service import (
            ChatSqlVisualizationAdvisorService,
        )
        from app.domain.services.chat_sql_optimization_advisor_service import (
            ChatSqlOptimizationAdvisorService,
        )
        from app.domain.services.chat_sql_query_pattern_advisor_service import (
            ChatSqlQueryPatternAdvisorService,
        )

        result_analysis = ChatSqlResultAnalyzerService.analyze_tool_calls(tool_calls)
        visualization = ChatSqlVisualizationAdvisorService.recommend(
            message=message,
            mode=mode,
            result_analysis=result_analysis,
        )
        pattern_advice = ChatSqlQueryPatternAdvisorService.recommend(message)
        optimization = None

        if sql_text and mode in {"optimize", "review", "execute", "create"}:
            optimization = ChatSqlOptimizationAdvisorService.advise(
                str(sql_text),
                dialect=str(dialect["dialect"]),
                mode=mode,
            )

        from app.domain.services.chat_sql_authoring_guidance_service import (
            ChatSqlAuthoringGuidanceService,
        )

        agent_actions = ChatSqlAuthoringGuidanceService.agent_actions_available(workspace_context)

        return {
            "mode": mode,
            "dialect": dialect,
            "workspace": workspace,
            "agentActionsAvailable": agent_actions,
            "plannerHints": cls.build_planner_hints(message) + list(pattern_advice.get("hints") or []),
            "patternAdvice": pattern_advice,
            "performance": performance,
            "optimization": optimization,
            "review": review,
            "blocked": blocked,
            "resultAnalysis": result_analysis,
            "visualizationAdvice": visualization,
            "schemaDiscovery": schema_discovery,
            "schemaPrefetchRecommended": cls.should_prefetch_schema(
                message=message,
                mode=mode,
                workspace_context=workspace_context,
                previous_messages=previous_messages,
            ),
        }

    @classmethod
    def build_planner_hints(cls, message: str | None) -> list[str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return []

        hints: list[str] = []

        for patterns, hint in _PLANNER_HINTS:
            if any(pattern in normalized for pattern in patterns):
                hints.append(hint)

        if re.search(r"\bjoin\b", normalized):
            hints.append("check_join_granularity")

        return hints

    @classmethod
    def should_prefetch_schema(
        cls,
        *,
        message: str | None,
        mode: SqlSpecialistMode | None = None,
        workspace_context: dict | None = None,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        if not cls._sql_authoring_enabled(workspace_context):
            return False

        resolved_mode = mode or cls.classify_mode(message, previous_messages=previous_messages)

        from app.domain.services.chat_sql_authoring_guidance_service import (
            ChatSqlAuthoringGuidanceService,
        )

        if not ChatSqlAuthoringGuidanceService.agent_actions_available(workspace_context):
            return False

        if resolved_mode in {"schema_explore", "create", "incremental_edit"}:
            return True

        if resolved_mode == "review" and ChatSqlPerformanceAdvisorService.extract_sql_block(
            str(message or "")
        ):
            return True

        return ChatSqlAuthoringGuidanceService.should_prefetch_schema(
            message=str(message or ""),
            workspace_context=workspace_context,
            previous_messages=previous_messages,
        )

    @classmethod
    def requires_llm_response(cls, snapshot: dict[str, Any] | None) -> bool:
        if not snapshot:
            return False

        mode = str(snapshot.get("mode") or "none")

        if mode in {"create", "review", "explain", "optimize", "incremental_edit"}:
            return True

        if mode == "schema_explore":
            normalized = ChatMessageNormalizationService.normalize_for_matching(
                str(snapshot.get("message") or "")
            )

            return any(
                term in normalized
                for term in ("relacion", "join", "ligar", "associar", "chave", "fk ")
            )

        return False

    @classmethod
    def enrich_tool_context(
        cls,
        *,
        message: str,
        result: dict,
        workspace_context: dict | None = None,
        previous_messages: list[Any] | None = None,
    ) -> dict:
        snapshot = cls.build_pipeline_snapshot(
            message=message,
            workspace_context=workspace_context,
            previous_messages=previous_messages,
            tool_calls=result.get("toolCalls") if isinstance(result.get("toolCalls"), list) else None,
        )

        if not snapshot:
            return result

        updated = dict(result)
        snapshot = {**snapshot, "message": message}
        updated["sqlAdvanced"] = snapshot
        supplement = cls.build_prompt_supplement(snapshot)

        if supplement:
            existing = str(updated.get("context") or "").strip()
            updated["context"] = f"{existing}\n\n{supplement}".strip() if existing else supplement

        if cls.requires_llm_response(snapshot):
            updated.pop("directAnswer", None)
            updated["skipRag"] = False
            updated["sqlRequiresLlm"] = True
            updated = cls.strip_schema_catalog_presentations(updated)

        return updated

    @classmethod
    def is_schema_prefetch_path(cls, path: str | None) -> bool:
        lowered = str(path or "").lower()

        return "/system/tables" in lowered and (
            "/columns" in lowered or "/schema" in lowered or "/relations" in lowered
        )

    @classmethod
    def should_treat_schema_as_internal(cls, message: str | None, *, path: str | None) -> bool:
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        if not cls.is_schema_prefetch_path(path):
            return False

        if ChatSqlIntentService.is_authoring_request(message):
            return True

        mode = cls.classify_mode(message)

        return mode in {
            "create",
            "review",
            "explain",
            "optimize",
            "incremental_edit",
            "schema_explore",
        }

    @classmethod
    def annotate_schema_prefetch_tool_metadata(
        cls,
        message: str | None,
        metadata: dict | None,
    ) -> dict:
        meta = dict(metadata or {})

        if not cls.should_treat_schema_as_internal(message, path=str(meta.get("path") or "")):
            return meta

        meta["sqlSchemaPrefetch"] = True
        meta["suppressClientPresentation"] = True
        meta["preferredFormat"] = "text"
        meta["currentMessage"] = str(message or "")

        return meta

    @classmethod
    def strip_schema_catalog_presentations(cls, result: dict) -> dict:
        updated = dict(result)
        tool_calls = updated.get("toolCalls")

        if not isinstance(tool_calls, list):
            return updated

        stripped_calls: list[dict] = []

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                stripped_calls.append(tool_call)
                continue

            item = dict(tool_call)
            metadata = dict(item.get("metadata") or {})

            if (
                metadata.get("sqlSchemaPrefetch")
                or metadata.get("suppressClientPresentation")
                or cls.is_schema_prefetch_path(str(metadata.get("path") or ""))
            ):
                for key in (
                    "presentation",
                    "tablePresentation",
                    "textPresentation",
                    "treePresentation",
                    "chartPresentation",
                    "presentationDecision",
                ):
                    metadata.pop(key, None)

                metadata["suppressClientPresentation"] = True

            item["metadata"] = metadata
            stripped_calls.append(item)

        updated["toolCalls"] = stripped_calls

        return updated

    @classmethod
    def compact_schema_prefetch_context(
        cls,
        *,
        message: str | None,
        data: object,
        metadata: dict | None,
    ) -> dict[str, object]:
        path = str((metadata or {}).get("path") or "")
        table_match = re.search(r"/system/tables/([A-Za-z0-9]+)", path, flags=re.IGNORECASE)
        table_name = table_match.group(1).upper() if table_match else "tabela"

        if "/relations" in path.lower():
            from app.domain.services.chat_sql_schema_discovery_service import (
                ChatSqlSchemaDiscoveryService,
            )

            payload = data.get("data") if isinstance(data, dict) and "data" in data else data
            relations = ChatSqlSchemaDiscoveryService._parse_relation_results(
                payload if isinstance(payload, dict) else {}
            )
            relation_lines = [
                (
                    f"{item['sourceTable']}.{item['sourceField']} → "
                    f"{item['targetTable']}.{item['targetField']}"
                )
                for item in relations[:10]
                if isinstance(item, dict)
            ]
            example_sql = cls._example_join_sql_for_tables([table_name, "SA1", "SC5"])

            return {
                "titulo": f"Relações internas {table_name} (não exibir catálogo ao usuário)",
                "linhas": [
                    f"Tabela consultada: {table_name} — {len(relation_lines)} relação(ões) no SX9.",
                    *(
                        [f"FK: {line}" for line in relation_lines]
                        if relation_lines
                        else ["Sem FK retornada — use convenção Protheus SC5.C5_CLIENTE = SA1.A1_COD."]
                    ),
                    "Entrega obrigatória: bloco ```sql``` com JOIN de exemplo (SELECT somente leitura).",
                    *( [f"Modelo: {example_sql}"] if example_sql else [] ),
                ],
            }

        columns = cls._extract_column_names_from_schema_payload(data)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        prioritized: list[str] = []

        for token in ("a1_cod", "a1_nome", "d_e_l_e_t_", "cod", "nome", "ativo"):
            for column in columns:
                if token in column.lower() and column not in prioritized:
                    prioritized.append(column)

        for column in columns:
            if column not in prioritized:
                prioritized.append(column)

            if len(prioritized) >= 12:
                break

        active_hint = (
            "Filtro Protheus usual para ativos: D_E_L_E_T_ = '' (ou equivalente na tabela física, ex. SA1010)."
            if "ativ" in normalized
            else "Use exclusão lógica D_E_L_E_T_ = '' quando aplicável."
        )

        return {
            "titulo": f"Schema interno {table_name} (não exibir catálogo ao usuário)",
            "linhas": [
                f"Tabela: {table_name} — {len(columns)} coluna(s) no catálogo.",
                f"Colunas para o SQL: {', '.join(prioritized) if prioritized else 'validar no SX3'}.",
                active_hint,
                "Entrega obrigatória ao usuário: bloco ```sql``` com SELECT (somente leitura), depois explicação curta.",
                "Use exatamente estes nomes de coluna no SQL (não invente Codigo/Nome/Status genéricos).",
                "Não responda apenas com tabela de metadados/colunas — isso foi prefetch interno.",
            ],
        }

    @classmethod
    def _example_join_sql_for_tables(cls, tables: list[str]) -> str | None:
        upper = {str(item).upper() for item in tables if item}

        if {"SC5", "SA1"}.issubset(upper):
            return (
                "SELECT SC5.C5_NUM, SC5.C5_CLIENTE, SA1.A1_COD, SA1.A1_NOME\n"
                "FROM SC5010 SC5\n"
                "INNER JOIN SA1010 SA1 ON SA1.A1_COD = SC5.C5_CLIENTE AND SA1.D_E_L_E_T_ = ''\n"
                "WHERE SC5.D_E_L_E_T_ = ''"
            )

        return None

    @classmethod
    def _extract_column_names_from_schema_payload(cls, data: object) -> list[str]:
        payload = data

        if isinstance(data, dict) and "data" in data:
            payload = data.get("data")

        if isinstance(payload, dict) and "results" in payload:
            payload = payload.get("results")

        if not isinstance(payload, list):
            return []

        names: list[str] = []

        for row in payload:
            if not isinstance(row, dict):
                continue

            field = (
                row.get("X3_CAMPO")
                or row.get("x3_campo")
                or row.get("campo")
                or row.get("CAMPO")
            )

            if field:
                names.append(str(field).strip())

        return names

    @classmethod
    def build_prompt_supplement(cls, snapshot: dict[str, Any]) -> str:
        mode = str(snapshot.get("mode") or "create")
        dialect = snapshot.get("dialect") if isinstance(snapshot.get("dialect"), dict) else {}
        workspace = snapshot.get("workspace") if isinstance(snapshot.get("workspace"), dict) else {}
        hints = snapshot.get("plannerHints") if isinstance(snapshot.get("plannerHints"), list) else []
        performance = snapshot.get("performance") if isinstance(snapshot.get("performance"), dict) else {}
        review = snapshot.get("review") if isinstance(snapshot.get("review"), dict) else None
        result_analysis = (
            snapshot.get("resultAnalysis") if isinstance(snapshot.get("resultAnalysis"), dict) else None
        )
        visualization = (
            snapshot.get("visualizationAdvice")
            if isinstance(snapshot.get("visualizationAdvice"), dict)
            else None
        )
        optimization = (
            snapshot.get("optimization") if isinstance(snapshot.get("optimization"), dict) else None
        )
        pattern_advice = (
            snapshot.get("patternAdvice") if isinstance(snapshot.get("patternAdvice"), dict) else None
        )

        agent_actions = bool(snapshot.get("agentActionsAvailable"))

        lines = [
            "[Especialista SQL Avançado]",
            f"Modo: {mode}",
            f"Dialeto: {dialect.get('dialect')} ({'assumido' if dialect.get('assumed') else 'informado'})",
            f"Limite/paginação: {dialect.get('limitSyntax')}",
        ]

        if not agent_actions:
            lines.append(
                "Chat base (sem agente/actions): elabore/revise/explique SQL em ```sql```; "
                "não chame API. Oriente ativar agente com POST /data/sql e /system/tables/* "
                "para executar ou validar schema."
            )

        if workspace.get("currentSql"):
            lines.append("Query ativa na sessão — prefira editar incrementalmente.")
            lines.append(f"Tabelas detectadas: {', '.join(workspace.get('tableNames') or []) or 'n/d'}")

        schema_discovery = snapshot.get("schemaDiscovery") if isinstance(snapshot.get("schemaDiscovery"), dict) else {}

        if schema_discovery.get("tableCandidates"):
            lines.append(
                f"Tabelas candidatas da mensagem: {', '.join(schema_discovery.get('tableCandidates') or [])}"
            )

        example_join = cls._example_join_sql_for_tables(
            [str(item) for item in (schema_discovery.get("tableCandidates") or [])]
        )

        if example_join and mode == "schema_explore":
            lines.append(
                "Inclua no bloco ```sql``` um JOIN de validação com base neste modelo (ajuste sufixo 010):"
            )
            lines.append(example_join)

        if schema_discovery.get("columnCandidates"):
            lines.append(
                f"Colunas/contexto de coluna detectadas: {', '.join(schema_discovery.get('columnCandidates') or [])}"
            )

        if schema_discovery.get("domainHint"):
            lines.append(f"Domínio semântico detectado: {schema_discovery.get('domainHint')}")

        from app.domain.services.chat_sql_semantic_schema_mapper_service import (
            ChatSqlSemanticSchemaMapperService,
        )
        from app.domain.services.chat_sql_relationship_resolver_service import (
            ChatSqlRelationshipResolverService,
        )

        for hint in ChatSqlSemanticSchemaMapperService.format_hints(
            schema_discovery.get("semanticMapping")
        ):
            lines.append(f"Mapeamento: {hint}")

        for hint in ChatSqlRelationshipResolverService.format_hints(
            schema_discovery.get("relationships")
        ):
            lines.append(hint)

        if hints:
            lines.append(f"Dicas de planejamento: {', '.join(str(item) for item in hints)}")

        issues = performance.get("issues") or []

        if issues:
            lines.append("Alertas de performance:")

            for issue in issues[:4]:
                if isinstance(issue, dict):
                    lines.append(f"- {issue.get('message')}")

        if review and review.get("checklist"):
            lines.append(f"Revisão — risco {review.get('riskLevel')}:")

            for item in review.get("checklist") or []:
                if isinstance(item, dict) and item.get("status") in {"fail", "warn"}:
                    lines.append(f"- [{item.get('status')}] {item.get('detail')}")

        if snapshot.get("blocked"):
            lines.append("BLOQUEIO: comando destrutivo detectado — recuse execução.")

        if result_analysis:
            lines.append(f"Registros retornados: {result_analysis.get('rowCount', 'n/d')}")

            for insight in result_analysis.get("insights") or []:
                lines.append(f"- {insight}")

            if result_analysis.get("isEmpty"):
                lines.append("Recuperação sugerida: ampliar período, revisar filtros ou validar schema.")

        if mode in {"create", "review", "explain", "optimize", "incremental_edit"} or (
            mode == "schema_explore" and cls.requires_llm_response(snapshot)
        ):
            lines.append(
                "ENTREGA OBRIGATÓRIA: responda com bloco ```sql``` contendo a consulta pedida "
                "(SELECT somente leitura) antes de qualquer outro conteúdo."
            )
            lines.append(
                "Prefetch GET /system/tables/* é contexto interno — não substitua o SQL por "
                "tabela/catálogo de colunas, salvo se o usuário pediu explicitamente «quais colunas» ou «schema»."
            )
            lines.append(
                "No Protheus use nomes reais das colunas (ex.: A1_COD, A1_NOME, D_E_L_E_T_ = '' para ativos); "
                "tabela física costuma ser sufixo 010 (SA1010) se o ambiente exigir."
            )
        elif visualization:
            lines.append(
                f"Visualização sugerida: {visualization.get('suggestedLabel')} "
                f"({visualization.get('reason')})"
            )

        if pattern_advice and pattern_advice.get("patterns"):
            lines.append("Padrões SQL recomendados:")

            for pattern in pattern_advice.get("patterns") or []:
                if isinstance(pattern, dict):
                    lines.append(f"- {pattern.get('guidance')}")

        if optimization and optimization.get("suggestions"):
            lines.append("Otimização:")

            for item in optimization.get("suggestions") or []:
                if isinstance(item, dict) and item.get("severity") in {"warn", "info"}:
                    lines.append(f"- {item.get('message')}")

        lines.append(
            "Regras: somente SELECT; valide schema via /system/tables/*; "
            "explique assunções; sugira próximo passo."
        )

        return "\n".join(lines)

    @classmethod
    def build_follow_up_suggestions(
        cls,
        *,
        message: str | None,
        snapshot: dict[str, Any] | None = None,
        tool_calls: list | None = None,
    ) -> list[dict[str, str]]:
        if snapshot is None:
            snapshot = cls.build_pipeline_snapshot(message=message, tool_calls=tool_calls)

        if not snapshot:
            return []

        mode = str(snapshot.get("mode") or "create")
        content = _interactivity_content()
        chips_by_mode = content.get("sqlAdvancedChips") or {}
        labels = chips_by_mode.get(mode) or chips_by_mode.get("default") or []
        queries = content.get("sqlAdvancedQueries") or {}
        workspace = snapshot.get("workspace") if isinstance(snapshot.get("workspace"), dict) else {}
        table_name = (workspace.get("tableNames") or ["{{tableName}}"])[0]
        result_analysis = (
            snapshot.get("resultAnalysis") if isinstance(snapshot.get("resultAnalysis"), dict) else None
        )
        visualization = (
            snapshot.get("visualizationAdvice")
            if isinstance(snapshot.get("visualizationAdvice"), dict)
            else None
        )
        suggestions: list[dict[str, str]] = []

        if isinstance(result_analysis, dict) and result_analysis.get("isEmpty"):
            from app.domain.services.chat_sql_result_analyzer_service import (
                ChatSqlResultAnalyzerService,
            )

            suggestions.extend(ChatSqlResultAnalyzerService.build_empty_recovery_follow_ups())

        for label in labels:
            if not isinstance(label, str) or not label.strip():
                continue

            template = queries.get(label, label)
            query = template.replace("{{tableName}}", table_name)

            suggestions.append({"label": label, "query": query})

        if visualization and isinstance(visualization.get("suggestedLabel"), str):
            label = str(visualization["suggestedLabel"]).strip()
            query = queries.get(label, f"gere um gráfico com os dados da última consulta")

            if label and not any(item.get("label") == label for item in suggestions):
                suggestions.insert(0, {"label": label, "query": query})

        return suggestions

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None,
        workspace_context: dict | None = None,
        previous_messages: list[Any] | None = None,
        tool_calls: list | None = None,
    ) -> None:
        snapshot = cls.build_pipeline_snapshot(
            message=message,
            workspace_context=workspace_context,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
        )

        if not snapshot:
            return

        metadata["sqlAdvanced"] = snapshot

    @classmethod
    def _sql_authoring_enabled(cls, workspace_context: dict | None) -> bool:
        skills = (workspace_context or {}).get("skills") or {}
        sql_authoring = skills.get("sqlAuthoring")

        if sql_authoring is None:
            from app.infrastructure.config.settings import Settings

            sql_authoring = Settings.CHAT_DEFAULT_SQL_AUTHORING_SKILL

        return bool(sql_authoring)
