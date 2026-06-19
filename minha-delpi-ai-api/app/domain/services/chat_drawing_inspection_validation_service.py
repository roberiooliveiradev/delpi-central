"""Validação de plano de inspeção (QP6/QP7/QP8) — contrato api-delpi."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)


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
    def row_header_summary(cls, row: dict[str, Any]) -> dict[str, str]:
        header = row.get("header") if isinstance(row.get("header"), dict) else {}
        qp6 = cls._inspection_field_list(row, "QP6", "qp6")
        header_desc = ""

        if qp6 and isinstance(qp6[0], dict):
            header_desc = str(qp6[0].get("QP6_DESCPO") or "").strip()

        return {
            "revision": str(header.get("revision") or "").strip(),
            "description": str(header.get("description") or header_desc or "").strip(),
            "inspection_type": str(header.get("inspection_type") or "").strip(),
        }

    @classmethod
    def flatten_measurable_rows(cls, row: dict[str, Any]) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        plan_keys = ChatDrawingPatternsService.inspection_plan_list_keys()
        legacy_keys = ChatDrawingPatternsService.inspection_legacy_plan_keys()

        measurable = cls._list_field(row, plan_keys[0]) if len(plan_keys) > 0 else []

        for test in measurable:
            if not isinstance(test, dict):
                continue

            rows.append(
                {
                    "operation": str(test.get("operation") or "").strip(),
                    "test": str(test.get("test_code") or test.get("sequence") or "").strip(),
                    "lab": str(test.get("labor") or "").strip(),
                    "nominal": str(test.get("nominal_value") or "").strip(),
                    "lower": str(test.get("lower_spec_limit") or "").strip(),
                    "upper": str(test.get("upper_spec_limit") or "").strip(),
                    "unit": str(test.get("unit") or "").strip(),
                }
            )

        if rows:
            return rows

        qp7 = cls._inspection_field_list(row, "QP7", "qp7")

        for test in qp7:
            if not isinstance(test, dict):
                continue

            rows.append(
                {
                    "operation": str(test.get("QP7_OPERAC") or "").strip(),
                    "test": str(test.get("QP7_ENSAIO") or "").strip(),
                    "lab": str(test.get("QP7_LABOR") or "").strip(),
                    "nominal": str(test.get("QP7_NOMINA") or "").strip(),
                    "lower": str(
                        test.get("QP7_LIE") or test.get("QP7_LIC") or ""
                    ).strip(),
                    "upper": str(
                        test.get("QP7_LSE") or test.get("QP7_LSC") or ""
                    ).strip(),
                    "unit": str(test.get("QP7_UNIMED") or "").strip(),
                }
            )

        return rows

    @classmethod
    def flatten_textual_rows(cls, row: dict[str, Any]) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        plan_keys = ChatDrawingPatternsService.inspection_plan_list_keys()
        textual = cls._list_field(row, plan_keys[1]) if len(plan_keys) > 1 else []

        for test in textual:
            if not isinstance(test, dict):
                continue

            rows.append(
                {
                    "operation": str(test.get("operation") or "").strip(),
                    "test": str(test.get("test_code") or test.get("sequence") or "").strip(),
                    "text": str(test.get("text") or "").strip(),
                }
            )

        if rows:
            return rows

        qp8 = cls._inspection_field_list(row, "QP8", "qp8")

        for test in qp8:
            if not isinstance(test, dict):
                continue

            rows.append(
                {
                    "operation": str(test.get("QP8_OPERAC") or "").strip(),
                    "test": str(test.get("QP8_ENSAIO") or "").strip(),
                    "text": str(test.get("QP8_TEXTO") or "").strip(),
                }
            )

        return rows

    @classmethod
    def flatten_export_rows(cls, row: dict[str, Any]) -> list[dict[str, str]]:
        product_code = cls.row_product_code(row)
        level = cls.row_level(row)
        level_text = "" if level is None else str(level)
        section_dimensional = ChatDrawingValidationContentService.get(
            "export",
            "inspectionReport",
            "sectionDimensional",
        )
        section_textual = ChatDrawingValidationContentService.get(
            "export",
            "inspectionReport",
            "sectionTextual",
        )
        rows: list[dict[str, str]] = []

        for test in cls.flatten_measurable_rows(row):
            rows.append(
                {
                    "product": product_code,
                    "level": level_text,
                    "section": section_dimensional,
                    "operation": test.get("operation", ""),
                    "test": test.get("test", ""),
                    "lab": test.get("lab", ""),
                    "nominal": test.get("nominal", ""),
                    "lower": test.get("lower", ""),
                    "upper": test.get("upper", ""),
                    "unit": test.get("unit", ""),
                    "detail": "",
                }
            )

        for test in cls.flatten_textual_rows(row):
            rows.append(
                {
                    "product": product_code,
                    "level": level_text,
                    "section": section_textual,
                    "operation": test.get("operation", ""),
                    "test": test.get("test", ""),
                    "lab": "",
                    "nominal": "",
                    "lower": "",
                    "upper": "",
                    "unit": "",
                    "detail": test.get("text", ""),
                }
            )

        return rows

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
    def _inspection_field_list(cls, row: dict[str, Any], *keys: str) -> list[Any]:
        for key in keys:
            value = row.get(key)

            if isinstance(value, list):
                return value

        return []

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
