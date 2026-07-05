"""Delegate — especialista SQL avançado."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from app.domain.services.chat_message_normalization_service import ChatMessageNormalizationService
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_intent_vocabulary_service import ChatSqlIntentVocabularyService
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_constants import (
    SQL_BLOCK_RE as _SQL_BLOCK_RE,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_facade_access import (
    sql_specialist_service,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_types import (
    SqlSpecialistMode,
    _interactivity_content,
)



class ChatAdvancedSqlSpecialistPromptService:
    @classmethod
    def _column_hints_from_prefetch(cls, tool_calls: list | None) -> list[str]:
        hints: list[str] = []

        if not isinstance(tool_calls, list):
            return hints

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue

            metadata = tool_call.get("metadata") or {}

            if not (
                metadata.get("sqlSchemaPrefetch")
                or sql_specialist_service().is_schema_prefetch_path(str(metadata.get("path") or ""))
            ):
                continue

            summary = metadata.get("humanizedSummary")

            if isinstance(summary, dict):
                for line in summary.get("linhas") or []:
                    match = re.search(
                        r"Colunas para o SQL:\s*([^.]+)",
                        str(line),
                        flags=re.IGNORECASE,
                    )

                    if match:
                        for part in str(match.group(1)).split(","):
                            token = part.strip()

                            if token and token not in hints:
                                hints.append(token)

            path = str(metadata.get("path") or "").lower()

            if "/tables/sa1" in path:
                for token in ("A1_COD", "A1_NOME", "D_E_L_E_T_"):
                    if token not in hints:
                        hints.append(token)

            if "/tables/sb1" in path or (
                metadata.get("sqlSchemaPrefetch")
                and cls._authoring_context(message=str(metadata.get("currentMessage") or "")).get(
                    "logicalTable"
                )
                == "SB1"
            ):
                for token in ("B1_COD", "B1_DESC", "B1_GRUPO", "D_E_L_E_T_"):
                    if token not in hints:
                        hints.append(token)

        return hints

    @classmethod
    def _authoring_context(cls, *, message: str | None, columns: list[str] | None = None) -> dict[str, Any]:
        from app.domain.services.chat_sql_semantic_schema_mapper_service import (
            ChatSqlSemanticSchemaMapperService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        mapping = ChatSqlSemanticSchemaMapperService.map_message(message)
        logical_table = "SA1"
        code_col = "A1_COD"
        name_col = "A1_NOME"
        group_col: str | None = None

        for item in mapping.get("matches") or []:
            table_hints = item.get("tableHints") or []

            if table_hints:
                logical_table = str(table_hints[0]).upper()
                break

        explicit = re.search(
            r"\b(?:sa|sb|sc|sd|se|sf|sg|sh|si|sj|sk|sl|sm|sn|so|sp)[a-z]?\d{0,4}\b",
            normalized,
            flags=re.IGNORECASE,
        )

        if explicit:
            logical_table = explicit.group(0).upper()

        if logical_table.startswith("SB"):
            code_col = "B1_COD"
            name_col = "B1_DESC"
            group_col = "B1_GRUPO"
        elif logical_table.startswith("SA"):
            code_col = "A1_COD"
            name_col = "A1_NOME"

        column_list = list(columns or [])

        if column_list:
            code_col = next(
                (c for c in column_list if "cod" in c.lower()),
                code_col,
            )
            name_col = next(
                (
                    c
                    for c in column_list
                    if (
                        "nome" in c.lower()
                        or "desc" in c.lower()
                        or "name" in c.lower()
                    )
                    and "cod" not in c.lower()
                ),
                name_col,
            )
            group_col = next(
                (c for c in column_list if "grupo" in c.lower()),
                group_col,
            )

        physical = (
            logical_table
            if re.search(r"\d{3}$", logical_table)
            else f"{logical_table}010"
        )

        top_limit: int | None = None
        top_match = re.search(r"\btop\s+(\d+)\b", normalized, flags=re.IGNORECASE)

        if top_match:
            top_limit = int(top_match.group(1))
        else:
            count_match = re.search(
                r"\b(?:liste|listar|list|traga|mostre|retorne)\s+(\d+)\s+",
                normalized,
                flags=re.IGNORECASE,
            )

            if count_match:
                top_limit = int(count_match.group(1))

        group_value: str | None = None
        group_match = re.search(r"\bgrupo\s+(\d+)\b", normalized, flags=re.IGNORECASE)

        if group_match:
            group_value = group_match.group(1)

        return {
            "logicalTable": logical_table,
            "physicalTable": physical,
            "codeColumn": code_col,
            "nameColumn": name_col,
            "groupColumn": group_col,
            "groupValue": group_value,
            "topLimit": top_limit,
        }

    @classmethod
    def _authoring_sql_from_message(cls, message: str | None, columns: list[str]) -> str | None:
        ctx = cls._authoring_context(message=message, columns=columns)
        select_prefix = (
            f"SELECT TOP {ctx['topLimit']} "
            if ctx.get("topLimit")
            else "SELECT "
        )
        select_cols = [str(ctx["codeColumn"])]

        if ctx.get("nameColumn") and ctx["nameColumn"] not in select_cols:
            select_cols.append(str(ctx["nameColumn"]))

        lines = [
            f"{select_prefix}{', '.join(select_cols)}",
            f"FROM {ctx['physicalTable']}",
            "WHERE D_E_L_E_T_ = ''",
        ]

        if ctx.get("groupColumn") and ctx.get("groupValue"):
            lines.append(f"  AND {ctx['groupColumn']} = '{ctx['groupValue']}'")

        return "\n".join(lines)

    @classmethod
    def _authoring_sql_domain_mismatch(cls, *, message: str | None, sql_block: str) -> bool:
        ctx = cls._authoring_context(message=message)
        logical = str(ctx.get("logicalTable") or "").upper()
        sql_lower = sql_block.lower()

        if logical.startswith("SB"):
            return (
                "sa1010" in sql_lower
                or "a1_cod" in sql_lower
                or re.search(r"\ba1_[a-z0-9_]+\b", sql_lower) is not None
            )

        if logical.startswith("SA"):
            return (
                "sb1010" in sql_lower
                or "b1_cod" in sql_lower
                or re.search(r"\bb1_[a-z0-9_]+\b", sql_lower) is not None
            )

        return False

    @classmethod
    def ensure_required_sql_block(
        cls,
        answer: str | None,
        *,
        snapshot: dict[str, Any] | None,
    ) -> str:
        text = str(answer or "").strip()

        if not text or "```sql" in text.lower():
            return text

        if not sql_specialist_service().requires_llm_response(snapshot):
            return text

        message = str((snapshot or {}).get("message") or "")
        columns = cls._column_hints_from_prefetch(
            (snapshot or {}).get("toolCalls") if isinstance(snapshot, dict) else None
        )
        authored = cls._authoring_sql_from_message(message, columns)

        if authored and snapshot and str(snapshot.get("mode") or "") in {
            "create",
            "incremental_edit",
        }:
            intro = ChatSqlIntentVocabularyService.text(
                "advancedSqlSpecialist",
                "authoringHints",
                "protheusPhysicalTable",
            )

            return f"{intro}\n\n```sql\n{authored}\n```\n\n{text}".strip() if text else (
                f"{intro}\n\n```sql\n{authored}\n```"
            )

        discovery = (
            snapshot.get("schemaDiscovery")
            if isinstance(snapshot, dict) and isinstance(snapshot.get("schemaDiscovery"), dict)
            else {}
        )
        example = cls._example_join_sql_for_tables(
            [str(item) for item in (discovery.get("tableCandidates") or [])]
        )

        if not example:
            return text

        return (
            "Segue um exemplo de JOIN para validar a relação no schema:\n\n"
            f"```sql\n{example}\n```\n\n{text}"
        ).strip()

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
            mode == "schema_explore" and sql_specialist_service().requires_llm_response(snapshot)
        ):
            lines.append(
                "ENTREGA OBRIGATÓRIA: responda com bloco ```sql``` contendo a consulta pedida "
                "(SELECT somente leitura) antes de qualquer outro conteúdo."
            )
            lines.append(
                "Prefetch GET /system/tables/* é contexto interno — não substitua o SQL por "
                "tabela/catálogo de colunas, salvo se o usuário pediu explicitamente «quais colunas» ou «schema»."
            )
            authoring_hint_key = "protheusPhysicalTable"
            mapping = schema_discovery.get("semanticMapping") if isinstance(schema_discovery, dict) else {}

            for item in (mapping or {}).get("matches") or []:
                term = str((item or {}).get("term") or "").lower()

                if term in {"produto", "produtos", "item", "sku"}:
                    authoring_hint_key = "productCadastro"
                    break

                if term in {"cliente", "clientes", "customer"}:
                    authoring_hint_key = "clientCadastro"
                    break

            lines.append(
                ChatSqlIntentVocabularyService.text(
                    "advancedSqlSpecialist",
                    "authoringHints",
                    authoring_hint_key,
                )
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

