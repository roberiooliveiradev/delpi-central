"""Referência de comprimento total PDF × SG1010 — evita confundir quantidade de peça (PC) com mm."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_bom_quantity_semantics_service import (
    ChatDrawingBomQuantitySemanticsService,
)
from app.domain.services.chat_drawing_intermediate_semantics_service import (
    ChatDrawingIntermediateSemanticsService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
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

        pa_reference = cls._resolve_from_product_description(root)
        intermediates = ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(
            root
        )

        if intermediates:
            reference = cls._resolve_from_intermediates(intermediates, items, root)

            if reference is not None:
                if (
                    pa_reference is not None
                    and ChatDrawingToleranceService.lengths_within_tolerance(
                        reference.length_mm,
                        pa_reference.length_mm,
                    )
                    is False
                ):
                    return pa_reference

                return reference

        if pa_reference is not None:
            return pa_reference

        if len(items) == 1:
            reference = cls._resolve_from_single_item(items[0])

            if reference is not None:
                return reference

        cable_reference = cls._resolve_from_cable_materials(root, items)

        if cable_reference is not None:
            return cable_reference

        return None

    @classmethod
    def _resolve_from_product_description(cls, root: dict) -> DrawingTotalLengthReference | None:
        length_mm = ChatDrawingIntermediateSemanticsService._product_description_length_mm(
            root
        )

        if length_mm is None:
            return None

        return DrawingTotalLengthReference(length_mm=length_mm, unit_label="mm")

    @classmethod
    def _resolve_from_cable_materials(
        cls,
        root: dict,
        items: list[dict[str, Any]],
    ) -> DrawingTotalLengthReference | None:
        batch_scale = ChatDrawingBomQuantitySemanticsService.batch_scale_for_root(root)
        cable_items = [
            item
            for item in items
            if isinstance(item, dict)
            and ChatDrawingBomQuantitySemanticsService.is_cable_material_code(
                str(item.get("code") or ""),
                str(item.get("description") or ""),
            )
        ]

        if len(cable_items) != 1:
            return None

        item = cable_items[0]
        quantity = item.get("quantity")

        if quantity is None:
            return None

        try:
            value = float(quantity)
        except (TypeError, ValueError):
            return None

        unit = cls._item_unit(item)
        per_piece_mm = ChatDrawingBomQuantitySemanticsService.per_piece_length_mm(
            quantity=value,
            unit=unit or "MT",
            batch_scale=batch_scale,
            item=item,
        )

        if per_piece_mm is None:
            return None

        return DrawingTotalLengthReference(length_mm=per_piece_mm, unit_label="mm")

    @classmethod
    def _resolve_from_intermediates(
        cls,
        rows: list[dict[str, Any]],
        items: list[dict[str, Any]],
        root: dict,
    ) -> DrawingTotalLengthReference | None:
        references: list[DrawingTotalLengthReference] = []

        for row in rows:
            reference_mm = cls._intermediate_reference_mm(row, root)

            if reference_mm is None:
                continue

            references.append(
                DrawingTotalLengthReference(length_mm=reference_mm, unit_label="mm")
            )

        if not references:
            for item in items:
                reference = cls._length_from_item_quantity(item, root)

                if reference is not None:
                    references.append(reference)

        if not references:
            return None

        unique_lengths = {round(reference.length_mm, 4) for reference in references}

        if len(unique_lengths) != 1:
            return None

        return references[0]

    @classmethod
    def _intermediate_reference_mm(cls, row: dict[str, Any], root: dict) -> float | None:
        length_mm = row.get("lengthMm")

        if length_mm is None:
            return None

        try:
            return float(length_mm)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _resolve_from_single_item(cls, item: dict[str, Any]) -> DrawingTotalLengthReference | None:
        code = ChatProductQueryIntentService.normalize_product_code(
            str(item.get("code") or "")
        )

        if code and ChatDrawingPatternsService.is_intermediate_family(code):
            return None

        return cls._length_from_item_quantity(item, {})

    @classmethod
    def _length_from_item_quantity(
        cls,
        item: dict[str, Any],
        root: dict,
    ) -> DrawingTotalLengthReference | None:
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
            batch_scale = ChatDrawingBomQuantitySemanticsService.batch_scale_for_root(root)
            total_mm = ChatDrawingBomQuantitySemanticsService.per_piece_length_mm(
                quantity=value,
                unit=unit,
                batch_scale=batch_scale,
                item=item,
            )

            if total_mm is not None:
                return DrawingTotalLengthReference(length_mm=total_mm, unit_label="mm")

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
