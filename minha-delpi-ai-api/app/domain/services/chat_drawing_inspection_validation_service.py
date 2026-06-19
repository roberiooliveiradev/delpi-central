"""Validação de plano de inspeção (QP6/QP7/QP8) — contrato api-delpi."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService


class ChatDrawingInspectionValidationService:
    @classmethod
    def has_inspection_plan(cls, inspection: dict[str, Any] | None) -> bool:
        if not isinstance(inspection, dict):
            return False

        items = inspection.get("items")

        if not isinstance(items, list) or not items:
            return False

        for row in items:
            if not isinstance(row, dict):
                continue

            if cls._row_has_legacy_qp_keys(row):
                return True

            if cls._row_has_measurable_or_textual_tests(row):
                return True

        return False

    @classmethod
    def count_inspection_rows(cls, inspection: dict[str, Any] | None) -> int:
        if not isinstance(inspection, dict):
            return 0

        items = inspection.get("items")

        if not isinstance(items, list):
            return 0

        return len(items)

    @classmethod
    def _row_has_legacy_qp_keys(cls, row: dict[str, Any]) -> bool:
        for key in ChatDrawingPatternsService.inspection_legacy_plan_keys():
            if row.get(key):
                return True

        return False

    @classmethod
    def _row_has_measurable_or_textual_tests(cls, row: dict[str, Any]) -> bool:
        for key in ChatDrawingPatternsService.inspection_plan_list_keys():
            tests = row.get(key)

            if isinstance(tests, list) and tests:
                return True

        return False
