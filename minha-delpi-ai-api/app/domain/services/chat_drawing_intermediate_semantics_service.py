"""Semântica de códigos intermediários 50xx — comprimento e decapes (engenharia DELPI)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingIntermediateSemanticsService:
    @classmethod
    def parse_description(cls, description: str) -> dict[str, float | None]:
        match = ChatDrawingPatternsService.intermediate_segment().search(str(description or ""))

        if not match:
            return {
                "lengthMm": None,
                "leftDecapeMm": None,
                "rightDecapeMm": None,
            }

        return {
            "lengthMm": ChatDrawingToleranceService.parse_mm(match.group(1)),
            "leftDecapeMm": ChatDrawingToleranceService.parse_mm(match.group(2)),
            "rightDecapeMm": ChatDrawingToleranceService.parse_mm(match.group(3)),
        }

    @classmethod
    def collect_structure_intermediates(cls, root: dict) -> list[dict[str, Any]]:
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        rows: list[dict[str, Any]] = []

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("code") or "")
            )

            if not code or not ChatDrawingPatternsService.is_intermediate_family(code):
                continue

            parsed = cls.parse_description(str(item.get("description") or ""))
            child_qty = cls._first_child_quantity(item)

            rows.append(
                {
                    "code": code,
                    "description": str(item.get("description") or ""),
                    "lengthMm": parsed.get("lengthMm") if parsed.get("lengthMm") is not None else child_qty,
                    "leftDecapeMm": parsed.get("leftDecapeMm"),
                    "rightDecapeMm": parsed.get("rightDecapeMm"),
                    "cableCode": cls._first_child_code(item),
                    "cableQuantityMm": child_qty,
                }
            )

        return rows

    @classmethod
    def _first_child_code(cls, item: dict) -> str | None:
        for child in item.get("components") or []:
            if not isinstance(child, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(child.get("code") or "")
            )

            if code:
                return code

        return None

    @classmethod
    def _first_child_quantity(cls, item: dict) -> float | None:
        for child in item.get("components") or []:
            if not isinstance(child, dict):
                continue

            quantity = child.get("quantity")

            if quantity is not None:
                try:
                    return float(quantity)
                except (TypeError, ValueError):
                    return None

        return None
