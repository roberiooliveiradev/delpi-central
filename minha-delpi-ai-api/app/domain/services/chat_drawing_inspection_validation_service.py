"""Validação de plano de inspeção (QP6/QP7/QP8) — contrato api-delpi."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService


class ChatDrawingInspectionValidationService:
    @classmethod
    def row_product_code(cls, row: dict[str, Any]) -> str:
        return str(row.get("product") or row.get("product_code") or "").strip()

    @classmethod
    def row_level(cls, row: dict[str, Any]) -> Any:
        if row.get("level") is not None:
            return row.get("level")

        if row.get("bom_level") is not None:
            return row.get("bom_level")

        return None

    @classmethod
    def row_plan_counts(cls, row: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
        legacy_keys = ChatDrawingPatternsService.inspection_legacy_plan_keys()
        plan_keys = ChatDrawingPatternsService.inspection_plan_list_keys()

        qp6_count: int | None = None
        qp7_count: int | None = None
        qp8_count: int | None = None

        if len(legacy_keys) > 0:
            qp6_legacy = cls._list_field(row, legacy_keys[0])

            if qp6_legacy:
                qp6_count = len(qp6_legacy)

        if qp6_count is None:
            header = row.get("header")

            if isinstance(header, dict) and any(
                header.get(key)
                for key in ("product_code", "description", "revision", "inspection_type")
            ):
                qp6_count = 1

        if len(plan_keys) > 0:
            measurable = cls._list_field(row, plan_keys[0])

            if measurable:
                qp7_count = len(measurable)

        if qp7_count is None and len(legacy_keys) > 1:
            qp7_legacy = cls._list_field(row, legacy_keys[1])

            if qp7_legacy:
                qp7_count = len(qp7_legacy)

        if len(plan_keys) > 1:
            textual = cls._list_field(row, plan_keys[1])

            if textual:
                qp8_count = len(textual)

        if qp8_count is None and len(legacy_keys) > 2:
            qp8_legacy = cls._list_field(row, legacy_keys[2])

            if qp8_legacy:
                qp8_count = len(qp8_legacy)

        return qp6_count, qp7_count, qp8_count

    @classmethod
    def row_has_inspection_data(cls, row: dict[str, Any]) -> bool:
        qp6_count, qp7_count, qp8_count = cls.row_plan_counts(row)

        if any(count for count in (qp6_count, qp7_count, qp8_count)):
            return True

        return cls._row_has_legacy_qp_keys(row) or cls._row_has_measurable_or_textual_tests(row)

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
    def _list_field(cls, row: dict[str, Any], key: str) -> list[Any]:
        value = row.get(key)

        return value if isinstance(value, list) else []

    @classmethod
    def _row_has_legacy_qp_keys(cls, row: dict[str, Any]) -> bool:
        for key in ChatDrawingPatternsService.inspection_legacy_plan_keys():
            if cls._list_field(row, key):
                return True

        return False

    @classmethod
    def _row_has_measurable_or_textual_tests(cls, row: dict[str, Any]) -> bool:
        for key in ChatDrawingPatternsService.inspection_plan_list_keys():
            if cls._list_field(row, key):
                return True

        return False
