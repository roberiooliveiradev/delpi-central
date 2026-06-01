"""Otimização SQL — Playbook Especialista §35–38, §106–111."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_sql_performance_advisor_service import (
    ChatSqlPerformanceAdvisorService,
)


class ChatSqlOptimizationAdvisorService:
    _JOIN_ON = re.compile(r"\bon\b\s+(.+?)(?:\bwhere\b|\bgroup\b|\border\b|\blimit\b|\btop\b|$)", re.I | re.S)
    _WHERE = re.compile(r"\bwhere\b(.+?)(?:\bgroup\b|\border\b|\blimit\b|\btop\b|$)", re.I | re.S)
    _ORDER = re.compile(r"\border\s+by\b(.+?)(?:\blimit\b|\btop\b|$)", re.I | re.S)

    @classmethod
    def advise(
        cls,
        sql: str | None,
        *,
        dialect: str = "generic",
        mode: str | None = None,
        explain_available: bool = False,
    ) -> dict[str, Any]:
        text = ChatSqlPerformanceAdvisorService.extract_sql_block(sql) or str(sql or "").strip()
        performance = ChatSqlPerformanceAdvisorService.analyze(text, dialect=dialect) if text else {
            "issues": [],
            "features": {},
            "score": None,
        }
        suggestions: list[dict[str, str]] = []

        for issue in performance.get("issues") or []:
            if isinstance(issue, dict):
                suggestions.append(
                    {
                        "code": str(issue.get("code") or "performance"),
                        "severity": str(issue.get("severity") or "info"),
                        "message": str(issue.get("message") or ""),
                        "category": "performance",
                    }
                )

        if text:
            suggestions.extend(cls._index_suggestions(text, dialect=dialect))

        explain = cls._explain_guidance(
            text,
            dialect=dialect,
            mode=mode,
            explain_available=explain_available,
        )

        if explain:
            suggestions.append(explain)

        refactor = cls._refactor_hints(text, performance.get("features") or {})

        for item in refactor:
            suggestions.append(item)

        high = sum(1 for item in suggestions if item.get("severity") == "warn")

        return {
            "suggestions": suggestions,
            "performance": performance,
            "explainRecommended": bool(explain),
            "indexCandidateColumns": cls._extract_filter_columns(text),
            "score": performance.get("score"),
            "priority": "high" if high >= 2 else "medium" if high else "low",
        }

    @classmethod
    def _index_suggestions(cls, sql: str, *, dialect: str) -> list[dict[str, str]]:
        output: list[dict[str, str]] = []
        filters = cls._extract_filter_columns(sql)
        joins = cls._extract_join_keys(sql)
        orders = cls._extract_order_columns(sql)

        for column in filters[:4]:
            output.append(
                {
                    "code": "index_filter_column",
                    "severity": "info",
                    "category": "index",
                    "message": f"Considere índice em `{column}` para acelerar filtros WHERE.",
                }
            )

        for column in joins[:3]:
            output.append(
                {
                    "code": "index_join_key",
                    "severity": "info",
                    "category": "index",
                    "message": f"Valide índice/chave em `{column}` usada no JOIN.",
                }
            )

        for column in orders[:2]:
            output.append(
                {
                    "code": "index_sort_column",
                    "severity": "info",
                    "category": "index",
                    "message": f"ORDER BY em `{column}` pode se beneficiar de índice compatível.",
                }
            )

        if dialect == "sqlserver" and "like '%" in sql.lower():
            output.append(
                {
                    "code": "leading_wildcard",
                    "severity": "warn",
                    "category": "index",
                    "message": "LIKE com curinga à esquerda tende a ignorar índice — avalie busca alternativa.",
                }
            )

        return output

    @classmethod
    def _explain_guidance(
        cls,
        sql: str,
        *,
        dialect: str,
        mode: str | None,
        explain_available: bool,
    ) -> dict[str, str] | None:
        if not sql or mode != "optimize":
            return None

        if explain_available:
            token = "SET SHOWPLAN_ALL ON" if dialect == "sqlserver" else "EXPLAIN"

            return {
                "code": "run_explain",
                "severity": "info",
                "category": "explain",
                "message": f"Ferramenta disponível — solicite plano com `{token}` antes de refatorar.",
            }

        return {
            "code": "explain_unavailable",
            "severity": "info",
            "category": "explain",
            "message": "EXPLAIN não disponível via ferramenta — revise filtros, joins e SELECT antes de refatorar.",
        }

    @classmethod
    def _refactor_hints(cls, sql: str, features: dict[str, Any]) -> list[dict[str, str]]:
        if not sql:
            return []

        hints: list[dict[str, str]] = []

        if not features.get("usesCte") and len(sql) > 280:
            hints.append(
                {
                    "code": "consider_cte",
                    "severity": "info",
                    "category": "refactor",
                    "message": "Consulta longa — CTEs podem melhorar legibilidade e manutenção.",
                }
            )

        if re.search(r"\(\s*select\b", sql, re.I) and not features.get("usesWindowFunction"):
            hints.append(
                {
                    "code": "consider_window",
                    "severity": "info",
                    "category": "refactor",
                    "message": "Subquery repetida — avalie window function (ROW_NUMBER/RANK) se for ranking/deduplicação.",
                }
            )

        return hints

    @classmethod
    def _extract_filter_columns(cls, sql: str) -> list[str]:
        match = cls._WHERE.search(sql)

        if not match:
            return []

        return cls._tokenize_columns(match.group(1))

    @classmethod
    def _extract_join_keys(cls, sql: str) -> list[str]:
        columns: list[str] = []

        for match in cls._JOIN_ON.finditer(sql):
            columns.extend(cls._tokenize_columns(match.group(1)))

        return cls._dedupe(columns)

    @classmethod
    def _extract_order_columns(cls, sql: str) -> list[str]:
        match = cls._ORDER.search(sql)

        if not match:
            return []

        return cls._tokenize_columns(match.group(1))

    @classmethod
    def _tokenize_columns(cls, fragment: str) -> list[str]:
        tokens: list[str] = []

        for piece in re.split(r"\band\b|\bor\b", fragment, flags=re.I):
            for match in re.finditer(r"\b([A-Za-z_][\w$]*)\.([A-Za-z_][\w$]*)\b", piece):
                tokens.append(f"{match.group(1)}.{match.group(2)}")

            for match in re.finditer(r"\b([A-Za-z_][\w$]{2,})\s*(?:=|<|>|<=|>=|<>|!=|like|in\b)", piece, re.I):
                name = match.group(1)

                if name.lower() not in {"and", "or", "not", "is", "null", "between"}:
                    tokens.append(name)

        return cls._dedupe(tokens)

    @classmethod
    def _dedupe(cls, items: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []

        for item in items:
            token = item.strip()

            if not token or token.lower() in seen:
                continue

            seen.add(token.lower())
            output.append(token)

        return output
