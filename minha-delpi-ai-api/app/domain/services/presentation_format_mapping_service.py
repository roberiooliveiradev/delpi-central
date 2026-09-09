"""Maps PresentationSpec format IDs to MFE column dataType / chart fieldFormats."""

from __future__ import annotations

from typing import Mapping

from app.domain.entities.presentation_spec import SUPPORTED_FORMATS

# MFE ChatRich* column/KPI dataType union (chatTypes.ts).
MFE_DATA_TYPES = frozenset(
    {
        "text",
        "number",
        "currency",
        "date",
        "percent",
        "quantity",
        "days",
    }
)

# Spec format (and common aliases) → MFE dataType.
_SPEC_TO_MFE_DATA_TYPE: dict[str, str] = {
    "currency": "currency",
    "percentage": "percent",
    "percent": "percent",
    "integer": "number",
    "decimal": "number",
    "number": "number",
    "date": "date",
    "datetime": "date",
    "duration": "days",
    "days": "days",
    "quantity": "quantity",
    "text": "text",
}

# Chart axis formatters (presentationFieldLabels.formatChartAxisValue) understand Spec-ish IDs.
_SPEC_TO_CHART_FIELD_FORMAT: dict[str, str] = {
    "currency": "currency",
    "percentage": "percentage",
    "percent": "percentage",
    "integer": "integer",
    "decimal": "decimal",
    "number": "decimal",
    "date": "date",
    "datetime": "date",
    "duration": "quantity",
    "days": "quantity",
    "quantity": "quantity",
}


class PresentationFormatMappingService:
    """Single owner for Spec format ↔ MFE dataType / chart fieldFormat."""

    @classmethod
    def to_mfe_data_type(cls, format_id: str | None) -> str | None:
        token = str(format_id or "").strip().lower()
        if not token:
            return None
        mapped = _SPEC_TO_MFE_DATA_TYPE.get(token)
        if mapped in MFE_DATA_TYPES:
            return mapped
        return None

    @classmethod
    def to_chart_field_format(cls, format_id: str | None) -> str | None:
        token = str(format_id or "").strip().lower()
        if not token:
            return None
        return _SPEC_TO_CHART_FIELD_FORMAT.get(token)

    @classmethod
    def map_column_data_types(cls, formats: Mapping[str, str] | None) -> dict[str, str]:
        if not formats:
            return {}
        mapped: dict[str, str] = {}
        for key, value in formats.items():
            field_key = str(key or "").strip()
            data_type = cls.to_mfe_data_type(value)
            if field_key and data_type:
                mapped[field_key] = data_type
        return mapped

    @classmethod
    def map_chart_field_formats(cls, formats: Mapping[str, str] | None) -> dict[str, str]:
        if not formats:
            return {}
        mapped: dict[str, str] = {}
        for key, value in formats.items():
            field_key = str(key or "").strip()
            chart_format = cls.to_chart_field_format(value)
            if field_key and chart_format:
                mapped[field_key] = chart_format
        return mapped

    @classmethod
    def is_supported_spec_format(cls, format_id: str | None) -> bool:
        token = str(format_id or "").strip().lower()
        return token in SUPPORTED_FORMATS
