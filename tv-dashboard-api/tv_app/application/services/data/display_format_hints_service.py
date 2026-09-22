"""Hints de formatação numérica/texto para projeções KPI/chart/table."""

from __future__ import annotations

import re
from typing import Any

from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)
from tv_app.domain.presentation_intelligence.models import FormatHint

_ALLOWED_VALUE_FORMATS = frozenset(
    {"auto", "number", "currency", "percent", "compact", "raw", "integer", "decimal", "plain"}
)
_ALLOWED_CATEGORIES = frozenset(
    {
        "general",
        "number",
        "currency",
        "accounting",
        "date",
        "time",
        "percent",
        "scientific",
        "text",
        "custom",
    }
)

_FIELD_PERCENT = re.compile(
    r"(pct|percent|percentage|percentual|taxa_|_rate$|share)",
    re.IGNORECASE,
)
_FIELD_CURRENCY = re.compile(
    r"(valor|value_brl|amount|revenue|receita|custo|cost|preco|price|fatur)",
    re.IGNORECASE,
)


class DisplayFormatHintsService:
    """Owner de FormatHint a partir de NL, nome de campo ou valueFieldTypes."""

    @classmethod
    def allowed_value_formats(cls) -> frozenset[str]:
        return _ALLOWED_VALUE_FORMATS

    @classmethod
    def allowed_categories(cls) -> frozenset[str]:
        return _ALLOWED_CATEGORIES

    @classmethod
    def is_valid_value_format(cls, raw: Any) -> bool:
        token = str(raw or "").strip().lower()
        return token in _ALLOWED_VALUE_FORMATS

    @classmethod
    def is_valid_category(cls, raw: Any) -> bool:
        token = str(raw or "").strip().lower()
        return token in _ALLOWED_CATEGORIES

    @classmethod
    def from_nl(cls, message: str) -> FormatHint | None:
        normalized = " ".join(str(message or "").strip().lower().split())
        if not normalized:
            return None
        for hint in PresentationOpsContentService.display_format_hints():
            markers = hint.get("markers")
            payload = hint.get("hint")
            if not isinstance(markers, list) or not isinstance(payload, dict):
                continue
            for marker in sorted(
                (str(m).strip().lower() for m in markers if str(m).strip()),
                key=len,
                reverse=True,
            ):
                if marker and marker in normalized:
                    return cls._from_payload(payload, source="nl")
        return None

    @classmethod
    def from_field_key(cls, field_key: str) -> FormatHint | None:
        key = str(field_key or "").strip()
        if not key:
            return None
        if _FIELD_PERCENT.search(key):
            return FormatHint(
                category="percent",
                value_format="percent",
                decimal_places=1,
                source="field_key",
            )
        if _FIELD_CURRENCY.search(key):
            return FormatHint(
                category="currency",
                value_format="currency",
                currency="BRL",
                decimal_places=2,
                source="field_key",
            )
        return None

    @classmethod
    def from_value_field_type(cls, field_type: str) -> FormatHint | None:
        token = str(field_type or "").strip().lower()
        if token in {"percent", "percentage", "pct"}:
            return FormatHint(
                category="percent",
                value_format="percent",
                decimal_places=1,
                source="value_field_type",
            )
        if token in {"currency", "money", "brl"}:
            return FormatHint(
                category="currency",
                value_format="currency",
                currency="BRL",
                decimal_places=2,
                source="value_field_type",
            )
        if token in {"number", "integer", "float", "decimal"}:
            return FormatHint(
                category="number",
                value_format="number",
                decimal_places=0 if token == "integer" else 2,
                source="value_field_type",
            )
        if token in {"text", "string"}:
            return FormatHint(category="text", value_format="raw", source="value_field_type")
        return None

    @classmethod
    def resolve(
        cls,
        *,
        message: str = "",
        field_key: str = "",
        field_type: str = "",
    ) -> FormatHint | None:
        return (
            cls.from_nl(message)
            or cls.from_value_field_type(field_type)
            or cls.from_field_key(field_key)
        )

    @classmethod
    def _from_payload(cls, payload: dict[str, Any], *, source: str) -> FormatHint | None:
        category = str(payload.get("category") or "").strip().lower()
        value_format = str(payload.get("valueFormat") or payload.get("value_format") or "").strip().lower()
        if not cls.is_valid_category(category) or not cls.is_valid_value_format(value_format):
            return None
        currency = str(payload.get("currency") or "").strip().upper() or None
        if currency and currency != "BRL":
            currency = "BRL"
        decimal_places = payload.get("decimalPlaces", payload.get("decimal_places"))
        places: int | None
        try:
            places = int(decimal_places) if decimal_places is not None else None
        except (TypeError, ValueError):
            places = None
        return FormatHint(
            category=category,
            value_format=value_format,
            currency=currency,
            decimal_places=places,
            source=source,
        )

    @classmethod
    def validate_projection_formats(cls, block: dict[str, Any]) -> list[str]:
        """Retorna códigos de erro se formatos inválidos aparecerem no bloco."""
        errors: list[str] = []
        kpi_opts = block.get("kpiOptions")
        if isinstance(kpi_opts, dict):
            vf = kpi_opts.get("valueFormat")
            if vf is not None and not cls.is_valid_value_format(vf):
                errors.append("kpiOptions.valueFormat")
            dvf = kpi_opts.get("displayValueFormat")
            if isinstance(dvf, dict):
                if not cls.is_valid_category(dvf.get("category")):
                    errors.append("kpiOptions.displayValueFormat.category")
        chart_opts = block.get("chartOptions")
        if isinstance(chart_opts, dict):
            vf = chart_opts.get("valueFormat")
            if vf is not None and not cls.is_valid_value_format(vf):
                errors.append("chartOptions.valueFormat")
        kpi_proj = block.get("kpiProjection")
        if isinstance(kpi_proj, dict):
            metrics = kpi_proj.get("metrics")
            if isinstance(metrics, list):
                for index, metric in enumerate(metrics):
                    if not isinstance(metric, dict):
                        continue
                    if metric.get("format") is not None and not cls.is_valid_value_format(
                        metric.get("format")
                    ):
                        errors.append(f"kpiProjection.metrics[{index}].format")
        table_proj = block.get("tableProjection")
        if isinstance(table_proj, dict):
            columns = table_proj.get("columns")
            if isinstance(columns, list):
                for index, column in enumerate(columns):
                    if not isinstance(column, dict):
                        continue
                    if column.get("valueFormat") is not None and not cls.is_valid_value_format(
                        column.get("valueFormat")
                    ):
                        errors.append(f"tableProjection.columns[{index}].valueFormat")
        return errors
