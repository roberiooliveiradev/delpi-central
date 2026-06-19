"""Semântica de códigos intermediários 50xx — comprimento e decapes (engenharia DELPI)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

# CT26VERM-00036/04/06-0000-0000 | CB1,50VERD-00255/06/06-6314-0111
_INTERMEDIATE_SEGMENT_RE = re.compile(
    r"(?:CT|CB|CA|CF|CV)\s*[\d,.]+[A-Z]{4}\s*-?\s*(\d+)\s*/\s*([\d,.]+)\s*/\s*([\d,.]+)",
    re.IGNORECASE,
)
_INTERMEDIATE_CODE_RE = re.compile(r"\b(50\d{6})\b")


class ChatDrawingIntermediateSemanticsService:
    @classmethod
    def parse_description(cls, description: str) -> dict[str, float | None]:
        match = _INTERMEDIATE_SEGMENT_RE.search(str(description or ""))

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

            if not code or not code.startswith("50"):
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
    def find_intermediate_codes_in_text(cls, text: str) -> list[str]:
        found: list[str] = []

        for match in _INTERMEDIATE_CODE_RE.finditer(str(text or "")):
            code = ChatProductQueryIntentService.normalize_product_code(match.group(1))

            if code and code not in found:
                found.append(code)

        return found

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
