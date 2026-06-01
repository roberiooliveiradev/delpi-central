"""Advisor de performance SQL — Playbook Especialista SQL Avançado §35–38."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatSqlPerformanceAdvisorService:
    _SELECT_STAR = re.compile(r"\bselect\s+\*", re.IGNORECASE)
    _DISTINCT = re.compile(r"\bselect\s+distinct\b", re.IGNORECASE)
    _FUNC_IN_WHERE = re.compile(
        r"\bwhere\b.+\b(year|month|day|datepart|date_format|to_char|upper|lower|trim)\s*\(",
        re.IGNORECASE | re.DOTALL,
    )
    _SUBQUERY_IN_SELECT = re.compile(
        r"\bselect\b.+\(\s*select\b",
        re.IGNORECASE | re.DOTALL,
    )
    _NO_LIMIT = re.compile(r"\b(limit|top|fetch\s+first)\b", re.IGNORECASE)
    _ORDER_WITHOUT_LIMIT = re.compile(
        r"\border\s+by\b(?:(?!limit|top|fetch\s+first).)*$",
        re.IGNORECASE | re.DOTALL,
    )
    _CTE = re.compile(r"\bwith\s+\w+\s+as\s*\(", re.IGNORECASE)
    _WINDOW = re.compile(
        r"\b(row_number|rank|dense_rank|ntile|lag|lead|sum|avg|count)\s*\([^)]*\)\s*over\s*\(",
        re.IGNORECASE,
    )

    @classmethod
    def analyze(cls, sql: str | None, *, dialect: str = "generic") -> dict[str, Any]:
        text = str(sql or "").strip()

        if not text:
            return {"issues": [], "features": {}, "score": None}

        issues: list[dict[str, str]] = []

        if cls._SELECT_STAR.search(text):
            issues.append(
                {
                    "code": "select_star",
                    "severity": "warn",
                    "message": "Evite SELECT * — liste colunas necessárias para reduzir I/O.",
                }
            )

        if cls._DISTINCT.search(text):
            issues.append(
                {
                    "code": "distinct_masking_join",
                    "severity": "warn",
                    "message": "DISTINCT pode mascarar join 1:N — revise granularidade.",
                }
            )

        if cls._FUNC_IN_WHERE.search(text):
            issues.append(
                {
                    "code": "function_on_filtered_column",
                    "severity": "warn",
                    "message": "Função em coluna filtrada pode impedir uso de índice.",
                }
            )

        if cls._SUBQUERY_IN_SELECT.search(text):
            issues.append(
                {
                    "code": "scalar_subquery",
                    "severity": "info",
                    "message": "Subquery escalar no SELECT — considere JOIN ou CTE.",
                }
            )

        if not cls._NO_LIMIT.search(text) and len(text) > 80:
            limit_token = "TOP" if dialect == "sqlserver" else "LIMIT"
            issues.append(
                {
                    "code": "missing_pagination",
                    "severity": "warn",
                    "message": f"Consulta ampla sem {limit_token} — aplique paginação segura.",
                }
            )

        if cls._ORDER_WITHOUT_LIMIT.search(text) and not cls._NO_LIMIT.search(text):
            issues.append(
                {
                    "code": "expensive_sort",
                    "severity": "info",
                    "message": "ORDER BY sem limite pode ser caro em conjuntos grandes.",
                }
            )

        features = {
            "usesCte": bool(cls._CTE.search(text)),
            "usesWindowFunction": bool(cls._WINDOW.search(text)),
        }

        warn_count = sum(1 for item in issues if item["severity"] == "warn")

        return {
            "issues": issues,
            "features": features,
            "score": max(0, 100 - warn_count * 15),
            "dialect": dialect,
        }

    @classmethod
    def analyze_message(cls, message: str | None, *, dialect: str = "generic") -> dict[str, Any]:
        sql = cls.extract_sql_block(message)

        if sql:
            return cls.analyze(sql, dialect=dialect)

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if normalized and any(
            token in normalized
            for token in ("lenta", "lento", "performance", "otimiz", "demorad")
        ):
            return {
                "issues": [
                    {
                        "code": "optimize_requested",
                        "severity": "info",
                        "message": "Modo otimização — revise índices, filtros sargáveis e joins.",
                    }
                ],
                "features": {},
                "score": None,
                "dialect": dialect,
            }

        return {"issues": [], "features": {}, "score": None, "dialect": dialect}

    @classmethod
    def extract_sql_block(cls, text: str | None) -> str | None:
        if not text:
            return None

        match = re.search(r"```sql\s*(.+?)```", text, flags=re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1).strip()

        if re.search(r"\bselect\b.+\bfrom\b", text, flags=re.IGNORECASE | re.DOTALL):
            return text.strip()

        return None
