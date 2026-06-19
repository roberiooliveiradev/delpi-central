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
            cable_code, cable_qty, cable_unit = cls._resolve_cable_child(item)

            rows.append(
                {
                    "code": code,
                    "description": str(item.get("description") or ""),
                    "lengthMm": parsed.get("lengthMm") if parsed.get("lengthMm") is not None else cable_qty,
                    "leftDecapeMm": parsed.get("leftDecapeMm"),
                    "rightDecapeMm": parsed.get("rightDecapeMm"),
                    "cableCode": cable_code,
                    "cableQuantityMm": cable_qty,
                    "cableUnit": cable_unit,
                }
            )

        return rows

    @classmethod
    def _resolve_cable_child(cls, item: dict) -> tuple[str | None, float | None, str | None]:
        cable_units = ChatDrawingPatternsService.cable_length_units()
        cable_child: dict | None = None
        fallback_child: dict | None = None

        for child in item.get("components") or []:
            if not isinstance(child, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(child.get("code") or "")
            )

            if not code:
                continue

            unit = cls._child_unit(child)

            if unit in cable_units:
                cable_child = child
                break

            if fallback_child is None:
                fallback_child = child

        selected = cable_child or fallback_child

        if not selected:
            return None, None, None

        quantity = selected.get("quantity")

        try:
            qty = float(quantity) if quantity is not None else None
        except (TypeError, ValueError):
            qty = None

        return (
            ChatProductQueryIntentService.normalize_product_code(
                str(selected.get("code") or "")
            )
            or None,
            qty,
            cls._child_unit(selected),
        )

    @classmethod
    def _child_unit(cls, child: dict) -> str | None:
        for key in ("unit", "component_unit", "unidade"):
            raw = child.get(key)

            if raw is None:
                continue

            value = str(raw).strip().upper()

            if value:
                return value

        return None
