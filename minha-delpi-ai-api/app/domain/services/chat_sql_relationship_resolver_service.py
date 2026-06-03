"""Resolução de relações e risco de duplicidade em joins — Playbook §16–18."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_sql_performance_advisor_service import (
    ChatSqlPerformanceAdvisorService,
)

_JOIN_TABLE_RE = re.compile(r"\b(?:from|join)\s+([A-Za-z0-9_]+)", re.IGNORECASE)
_ON_CLAUSE_RE = re.compile(
    r"\b(?:inner\s+join|left\s+join|right\s+join|join)\s+([A-Za-z0-9_]+)\s+on\s+([^;]+?)(?=\b(?:inner|left|right|join|where|group|order|limit|top)\b|$)",
    re.IGNORECASE | re.DOTALL,
)
_FK_SUFFIX_RE = re.compile(r"^([A-Z0-9]{2})_([A-Z0-9_]+)$")

# sufixo do campo → (tabela alvo típica Protheus, coluna chave)
_PROTHEUS_FK_HINTS: dict[str, tuple[str, str]] = {
    "CLIENTE": ("SA1", "A1_COD"),
    "FORNECE": ("SA2", "A2_COD"),
    "FORNEC": ("SA2", "A2_COD"),
    "PRODUTO": ("SB1", "B1_COD"),
    "PROD": ("SB1", "B1_COD"),
    "VEND": ("SA3", "A3_COD"),
    "VENDEDOR": ("SA3", "A3_COD"),
}


class ChatSqlRelationshipResolverService:
    @classmethod
    def resolve(
        cls,
        *,
        message: str | None = None,
        table_candidates: list[str] | None = None,
        schema_metadata: dict[str, Any] | None = None,
        current_sql: str | None = None,
    ) -> dict[str, Any]:
        metadata = schema_metadata if isinstance(schema_metadata, dict) else {}
        declared = cls._normalize_declared_relations(metadata.get("relations"))
        inferred = cls._infer_from_columns(metadata.get("tables") or {})
        join_clauses = cls._extract_join_clauses(current_sql)
        duplicate_risks = cls._assess_duplicate_risk(
            current_sql=current_sql,
            table_candidates=table_candidates,
            declared_count=len(declared),
        )
        suggestions = cls._build_join_suggestions(declared, inferred, join_clauses)

        return {
            "declaredRelations": declared,
            "inferredRelations": inferred,
            "existingJoins": join_clauses,
            "duplicateRisks": duplicate_risks,
            "joinSuggestions": suggestions,
            "hasRelations": bool(declared or inferred or join_clauses),
        }

    @classmethod
    def _normalize_declared_relations(cls, raw: Any) -> list[dict[str, str]]:
        if not isinstance(raw, list):
            return []

        output: list[dict[str, str]] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            source_table = str(item.get("sourceTable") or "").strip().upper()
            source_field = str(item.get("sourceField") or "").strip().upper()
            target_table = str(item.get("targetTable") or "").strip().upper()
            target_field = str(item.get("targetField") or "").strip().upper()

            if not source_table or not source_field or not target_table or not target_field:
                continue

            output.append(
                {
                    "sourceTable": source_table,
                    "sourceField": source_field,
                    "targetTable": target_table,
                    "targetField": target_field,
                    "confidence": "declared",
                    "label": f"{source_table}.{source_field} = {target_table}.{target_field}",
                }
            )

        return output

    @classmethod
    def _infer_from_columns(cls, tables: dict[str, Any]) -> list[dict[str, str]]:
        if not isinstance(tables, dict):
            return []

        inferred: list[dict[str, str]] = []
        table_codes = {name.upper() for name in tables}

        for table_name, table_info in tables.items():
            if not isinstance(table_info, dict):
                continue

            columns = table_info.get("columns")

            if not isinstance(columns, list):
                continue

            origin = str(table_name).strip().upper()

            for column in columns:
                if not isinstance(column, dict):
                    continue

                field = str(column.get("field") or "").strip().upper()
                match = _FK_SUFFIX_RE.match(field)

                if not match:
                    continue

                prefix, suffix = match.group(1), match.group(2)

                if len(origin) >= 2 and prefix == origin[:2]:
                    continue

                if suffix in {"FILIAL", "LOJA", "NUM", "ITEM", "SEQ", "ITEMPV"}:
                    continue

                target_hint = _PROTHEUS_FK_HINTS.get(suffix)

                if target_hint:
                    target, target_field = target_hint
                else:
                    target = prefix
                    target_field = f"{prefix}_COD"

                if target not in table_codes and origin not in table_codes:
                    continue

                label = f"{origin}.{field} ≈ {target}.{target_field}"
                key = label

                if any(item.get("label") == key for item in inferred):
                    continue

                inferred.append(
                    {
                        "sourceTable": origin,
                        "sourceField": field,
                        "targetTable": target,
                        "targetField": target_field,
                        "confidence": "inferred",
                        "label": label,
                    }
                )

        return inferred[:8]

    @classmethod
    def _extract_join_clauses(cls, current_sql: str | None) -> list[dict[str, str]]:
        sql = ChatSqlPerformanceAdvisorService.extract_sql_block(current_sql) or str(current_sql or "").strip()

        if not sql:
            return []

        clauses: list[dict[str, str]] = []

        for match in _ON_CLAUSE_RE.finditer(sql):
            table = match.group(1).strip().upper()
            condition = " ".join(match.group(2).split())

            if table and condition:
                clauses.append({"table": table, "on": condition})

        return clauses

    @classmethod
    def _assess_duplicate_risk(
        cls,
        *,
        current_sql: str | None,
        table_candidates: list[str] | None,
        declared_count: int,
    ) -> list[dict[str, str]]:
        sql = ChatSqlPerformanceAdvisorService.extract_sql_block(current_sql) or str(current_sql or "").strip()
        risks: list[dict[str, str]] = []
        tables = list(table_candidates or [])

        if sql:
            joined = _JOIN_TABLE_RE.findall(sql)

            if len(joined) >= 2 and "distinct" in sql.lower():
                risks.append(
                    {
                        "code": "distinct_masking_join",
                        "message": "DISTINCT com múltiplos JOINs pode mascarar duplicidade 1:N — prefira agregar antes do join.",
                    }
                )

            if len(joined) >= 3:
                risks.append(
                    {
                        "code": "multi_join_granularity",
                        "message": "Vários JOINs podem multiplicar linhas — confirme granularidade (agregar pedidos antes de juntar itens).",
                    }
                )

        if len(tables) >= 2 and declared_count == 0 and not sql:
            risks.append(
                {
                    "code": "validate_relations",
                    "message": "Múltiplas tabelas citadas sem relação validada — use GET /system/tables/{name}/relations antes do JOIN.",
                }
            )

        return risks

    @classmethod
    def _build_join_suggestions(
        cls,
        declared: list[dict[str, str]],
        inferred: list[dict[str, str]],
        join_clauses: list[dict[str, str]],
    ) -> list[str]:
        suggestions: list[str] = []

        for relation in declared[:6]:
            label = relation.get("label")

            if label:
                suggestions.append(f"FK declarada: {label}")

        for relation in inferred[:4]:
            label = relation.get("label")

            if label:
                suggestions.append(f"Relação inferida (validar): {label}")

        for clause in join_clauses[:4]:
            table = clause.get("table")
            condition = clause.get("on")

            if table and condition:
                suggestions.append(f"JOIN existente em {table}: {condition}")

        return suggestions

    @classmethod
    def format_hints(cls, resolution: dict[str, Any] | None) -> list[str]:
        if not isinstance(resolution, dict):
            return []

        lines = list(resolution.get("joinSuggestions") or [])

        for risk in resolution.get("duplicateRisks") or []:
            if isinstance(risk, dict) and risk.get("message"):
                lines.append(f"Risco: {risk['message']}")

        return lines
