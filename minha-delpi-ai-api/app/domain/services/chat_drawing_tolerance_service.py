"""Tolerâncias dimensionais para análise de desenhos — validation_rules DELPI."""

from __future__ import annotations


class ChatDrawingToleranceService:
    LENGTH_TOLERANCE_RATIO = 0.05
    DECAPE_TOLERANCE_MM = 1.0

    @classmethod
    def parse_mm(cls, value: str | float | int | None) -> float | None:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        normalized = str(value).strip().lower().replace(",", ".")

        if not normalized:
            return None

        for suffix in ("mm", "mi", "m"):
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)].strip()

        try:
            return float(normalized)
        except ValueError:
            return None

    @classmethod
    def lengths_within_tolerance(
        cls,
        pdf_mm: float | None,
        reference_mm: float | None,
        *,
        ratio: float | None = None,
    ) -> bool | None:
        pdf_value = cls.parse_mm(pdf_mm)
        ref_value = cls.parse_mm(reference_mm)

        if pdf_value is None or ref_value is None or ref_value <= 0:
            return None

        tolerance = ratio if ratio is not None else cls.LENGTH_TOLERANCE_RATIO
        delta = abs(pdf_value - ref_value) / ref_value

        return delta <= tolerance

    @classmethod
    def decape_within_tolerance(
        cls,
        pdf_mm: float | None,
        reference_mm: float | None,
        *,
        tolerance_mm: float | None = None,
    ) -> bool | None:
        pdf_value = cls.parse_mm(pdf_mm)
        ref_value = cls.parse_mm(reference_mm)

        if pdf_value is None or ref_value is None:
            return None

        limit = tolerance_mm if tolerance_mm is not None else cls.DECAPE_TOLERANCE_MM

        return abs(pdf_value - ref_value) <= limit
