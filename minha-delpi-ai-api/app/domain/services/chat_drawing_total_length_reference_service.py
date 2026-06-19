"""Referência de comprimento total PDF × SG1010 — evita confundir quantidade de peça (PC) com mm."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_intermediate_semantics_service import (
    ChatDrawingIntermediateSemanticsService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True, slots=True)
class DrawingTotalLengthReference:
    length_mm: float
    unit_label: str | None = None


class ChatDrawingTotalLengthReferenceService:
    @classmethod
    def resolve(cls, root: dict) -> DrawingTotalLengthReference | None:
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        items = [
            item
            for item in (structure.get("items") or [])
            if isinstance(item, dict)
        ]

        if not items:
            return None

        intermediates = ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(
            root
        )

        if intermediates:
            reference = cls._resolve_from_intermediates(intermediates, items)

            if reference is not None:
                return reference

        if len(items) == 1:
            return cls._resolve_from_single_item(items[0])

        return None

    @classmethod
    def _resolve_from_intermediates(
        cls,
        rows: list[dict[str, Any]],
        items: list[dict[str, Any]],
    ) -> DrawingTotalLengthReference | None:
        references: list[DrawingTotalLengthReference] = []

        for row in rows:
            length = row.get("cableQuantityMm")

            if length is None:
                length = row.get("lengthMm")

            if length is None:
                continue

            references.append(
                DrawingTotalLengthReference(
                    length_mm=float(length),
                    unit_label=str(row.get("cableUnit") or "mm").strip() or "mm",
                )
            )

        if not references:
            for item in items:
                reference = cls._length_from_item_quantity(item)

                if reference is not None:
                    references.append(reference)

        if not references:
            return None

        unique_lengths = {round(reference.length_mm, 4) for reference in references}

        if len(unique_lengths) != 1:
            return None

        if len(items) == 1 or len(references) == 1:
            return references[0]

        return references[0]

    @classmethod
    def _resolve_from_single_item(cls, item: dict[str, Any]) -> DrawingTotalLengthReference | None:
        code = ChatProductQueryIntentService.normalize_product_code(
            str(item.get("code") or "")
        )

        if code and ChatDrawingPatternsService.is_intermediate_family(code):
            return None

        return cls._length_from_item_quantity(item)

    @classmethod
    def _length_from_item_quantity(cls, item: dict[str, Any]) -> DrawingTotalLengthReference | None:
        quantity = item.get("quantity")

        if quantity is None:
            return None

        try:
            value = float(quantity)
        except (TypeError, ValueError):
            return None

        if value <= 0 or value > ChatDrawingPatternsService.max_root_structure_quantity_mm():
            return None

        unit = cls._item_unit(item)
        cable_units = ChatDrawingPatternsService.cable_length_units()
        piece_units = ChatDrawingPatternsService.piece_count_units()

        if unit in piece_units:
            return None

        if unit in cable_units:
            return DrawingTotalLengthReference(length_mm=value, unit_label=unit)

        if unit:
            return DrawingTotalLengthReference(length_mm=value, unit_label=unit)

        if value <= ChatDrawingPatternsService.max_piece_count_quantity():
            return None

        return DrawingTotalLengthReference(length_mm=value, unit_label="mm")

    @classmethod
    def _item_unit(cls, item: dict[str, Any]) -> str | None:
        for key in ("unit", "component_unit", "unidade"):
            raw = item.get(key)

            if raw is None:
                continue

            value = str(raw).strip().upper()

            if value:
                return value

        return None
