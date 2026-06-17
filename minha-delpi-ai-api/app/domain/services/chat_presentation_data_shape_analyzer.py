"""Análise de formato dos dados tabulares — Playbook 09."""

from __future__ import annotations

import re
from typing import Any

_TEMPORAL_LABEL_TOKENS = (
    "period",
    "periodo",
    "período",
    "month",
    "mes",
    "mês",
    "year",
    "ano",
    "date",
    "data",
    "week",
    "semana",
    "day",
    "dia",
)

_HIERARCHY_KEYS = frozenset(
    {
        "children",
        "child",
        "parent_id",
        "parentId",
        "parent_code",
        "parentCode",
        "level",
        "nivel",
        "depth",
        "bom",
    }
)

_DESCRIPTOR_KEY_HINTS = (
    "description",
    "descricao",
    "descrição",
    "name",
    "nome",
    "title",
    "titulo",
    "título",
    "product",
    "produto",
    "customer",
    "cliente",
    "supplier",
    "fornecedor",
    "branch",
    "filial",
    "warehouse",
    "armazem",
    "armazém",
    "unit",
    "unidade",
    "status",
    "situation",
    "situacao",
    "situação",
)

_IDENTIFIER_KEY_HINTS = (
    "op",
    "order",
    "pedido",
    "product",
    "produto",
    "code",
    "codigo",
    "código",
    "sku",
    "item",
    "invoice",
    "nota",
    "serial",
    "lote",
    "batch",
)


class ChatPresentationDataShapeAnalyzer:
    @classmethod
    def analyze(
        cls,
        *,
        rows: list[dict[str, Any]] | None,
        label_key: str | None = None,
    ) -> dict[str, Any]:
        safe_rows = [row for row in (rows or []) if isinstance(row, dict)]

        if not safe_rows:
            return {
                "rows": 0,
                "columns": 0,
                "hasDate": False,
                "hasNumeric": False,
                "hasCategory": False,
                "hasHierarchy": False,
                "numericKeys": [],
                "labelKey": None,
                "categoryCardinality": 0,
                "viewIntent": "unknown",
                "recommended": "text",
            }

        first = safe_rows[0]
        keys = list(first.keys())
        numeric_keys = [
            key
            for key, value in first.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ]
        string_keys = [key for key, value in first.items() if isinstance(value, str)]

        resolved_label = label_key or (string_keys[0] if string_keys else None)
        has_date = cls._has_temporal_column(keys, safe_rows, resolved_label)
        has_category = len(string_keys) >= 1 and len(numeric_keys) >= 1
        has_hierarchy = cls._has_hierarchy_hint(safe_rows, keys)
        category_cardinality = (
            len({str(row.get(resolved_label) or "") for row in safe_rows})
            if resolved_label
            else 0
        )

        recommended = cls._recommend_internal(
            rows=safe_rows,
            label_key=resolved_label,
            numeric_keys=numeric_keys,
            string_keys=string_keys,
            keys=keys,
            has_date=has_date,
            category_cardinality=category_cardinality,
            has_hierarchy=has_hierarchy,
        )
        view_intent = cls._classify_view_intent(
            rows=safe_rows,
            keys=keys,
            string_keys=string_keys,
            numeric_keys=numeric_keys,
            has_date=has_date,
            category_cardinality=category_cardinality,
            has_hierarchy=has_hierarchy,
        )

        return {
            "rows": len(safe_rows),
            "columns": len(keys),
            "hasDate": has_date,
            "hasNumeric": bool(numeric_keys),
            "hasCategory": has_category,
            "hasHierarchy": has_hierarchy,
            "numericKeys": numeric_keys[:6],
            "labelKey": resolved_label,
            "categoryCardinality": category_cardinality,
            "viewIntent": view_intent,
            "recommended": recommended,
        }

    @classmethod
    def _classify_view_intent(
        cls,
        *,
        rows: list[dict[str, Any]],
        keys: list[str],
        string_keys: list[str],
        numeric_keys: list[str],
        has_date: bool,
        category_cardinality: int,
        has_hierarchy: bool,
    ) -> str:
        if has_hierarchy:
            return "hierarchy"

        if len(rows) == 1 and len(numeric_keys) == 1:
            return "single_metric"

        if not numeric_keys:
            return "table_only"

        if has_date and numeric_keys:
            return "temporal_series"

        if cls._looks_like_auditable_list(keys=keys, string_keys=string_keys, row_count=len(rows)):
            return "auditable_list"

        if (
            len(string_keys) <= 2
            and 1 <= len(numeric_keys) <= 3
            and category_cardinality >= 2
        ):
            return "ranking"

        return "unknown"

    @classmethod
    def _looks_like_auditable_list(
        cls,
        *,
        keys: list[str],
        string_keys: list[str],
        row_count: int,
    ) -> bool:
        if len(string_keys) >= 3:
            return True

        if len(keys) >= 5 and len(string_keys) >= 2 and row_count >= 2:
            return True

        lowered = [str(key or "").lower() for key in keys]
        has_identifier = any(
            any(hint in token for hint in _IDENTIFIER_KEY_HINTS)
            for token in lowered
        )
        has_descriptor = any(
            any(hint in token for hint in _DESCRIPTOR_KEY_HINTS)
            for token in lowered
        )

        return has_identifier and has_descriptor and len(string_keys) >= 2

    @classmethod
    def _recommend_internal(
        cls,
        *,
        rows: list[dict[str, Any]],
        label_key: str | None,
        numeric_keys: list[str],
        string_keys: list[str],
        keys: list[str],
        has_date: bool,
        category_cardinality: int,
        has_hierarchy: bool,
    ) -> str:
        if has_hierarchy:
            return "tree"

        if len(rows) == 1 and len(numeric_keys) == 1:
            return "kpi"

        if not numeric_keys:
            return "table"

        if cls._looks_like_auditable_list(
            keys=keys,
            string_keys=string_keys,
            row_count=len(rows),
        ):
            return "table"

        if has_date and numeric_keys:
            return "line_chart"

        if category_cardinality > 6:
            return "horizontal_bar"

        if 3 <= category_cardinality <= 6 and len(numeric_keys) == 1:
            return "donut"

        if category_cardinality >= 2:
            return "horizontal_bar"

        return "table"

    @classmethod
    def _has_temporal_column(
        cls,
        keys: list[str],
        rows: list[dict[str, Any]],
        label_key: str | None,
    ) -> bool:
        for key in keys:
            token = str(key or "").lower()

            if any(part in token for part in _TEMPORAL_LABEL_TOKENS):
                return True

        if not label_key:
            return False

        samples = [
            str(row.get(label_key) or "").strip()
            for row in rows[:8]
            if row.get(label_key) not in (None, "")
        ]

        if not samples:
            return False

        date_like = sum(1 for value in samples if cls._looks_like_date_value(value))

        return date_like >= max(2, len(samples) // 2)

    @classmethod
    def _looks_like_date_value(cls, value: str) -> bool:
        token = str(value or "").strip()

        if not token:
            return False

        if re.fullmatch(r"\d{5,12}", token.replace(".", "")):
            return False

        return bool(
            re.search(r"\d{4}-\d{2}", token)
            or re.search(r"\d{1,2}/\d{1,2}", token)
            or re.search(
                r"\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\b",
                token,
                flags=re.IGNORECASE,
            )
        )

    @classmethod
    def _has_hierarchy_hint(cls, rows: list[dict[str, Any]], keys: list[str]) -> bool:
        lowered_keys = {str(key or "").lower() for key in keys}

        if lowered_keys & {token.lower() for token in _HIERARCHY_KEYS}:
            return True

        for row in rows[:5]:
            if isinstance(row.get("children"), list):
                return True

        return False
