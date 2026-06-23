"""Semântica de códigos intermediários 50xx — comprimento e decapes (engenharia DELPI)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_bom_quantity_semantics_service import (
    ChatDrawingBomQuantitySemanticsService,
)
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
        items = structure.get("items") if isinstance(structure.get("items"), list) else []
        rows: list[dict[str, Any]] = []

        def _walk(nodes: list[Any]) -> None:
            for item in nodes:
                if not isinstance(item, dict):
                    continue

                code = ChatProductQueryIntentService.normalize_product_code(
                    str(item.get("code") or "")
                )

                if code and ChatDrawingPatternsService.is_intermediate_family(code):
                    rows.append(cls._build_intermediate_row(item, root))

                components = item.get("components")

                if isinstance(components, list) and components:
                    _walk(components)

        _walk(items)
        return rows

    @classmethod
    def _build_intermediate_row(cls, item: dict[str, Any], root: dict) -> dict[str, Any]:
        parsed = cls.parse_description(str(item.get("description") or ""))
        cable_code, cable_qty, cable_unit, cable_child = cls._resolve_cable_child(item)
        length_mm = cls._resolve_length_mm(
            parsed=parsed,
            cable_qty=cable_qty,
            cable_unit=cable_unit,
            cable_child=cable_child,
            root=root,
        )

        return {
            "code": ChatProductQueryIntentService.normalize_product_code(
                str(item.get("code") or "")
            ),
            "description": str(item.get("description") or ""),
            "lengthMm": length_mm,
            "leftDecapeMm": parsed.get("leftDecapeMm"),
            "rightDecapeMm": parsed.get("rightDecapeMm"),
            "cableCode": cable_code,
            "cableQuantityMm": cable_qty,
            "cableUnit": cable_unit,
        }

    @classmethod
    def _resolve_length_mm(
        cls,
        *,
        parsed: dict[str, float | None],
        cable_qty: float | None,
        cable_unit: str | None,
        cable_child: dict[str, Any] | None,
        root: dict,
    ) -> float | None:
        pa_mm = cls._product_description_length_mm(root)
        parsed_mm = parsed.get("lengthMm")

        if pa_mm is not None and cls._product_description_declares_length(root):
            return pa_mm

        if (
            pa_mm is not None
            and parsed_mm is not None
            and ChatDrawingToleranceService.lengths_within_tolerance(pa_mm, parsed_mm)
            is False
        ):
            return pa_mm

        if parsed_mm is not None:
            return parsed_mm

        if cable_qty is not None:
            cable_units = ChatDrawingPatternsService.cable_length_units()
            unit = str(cable_unit or "").strip().upper()

            if unit in cable_units:
                batch_scale = ChatDrawingBomQuantitySemanticsService.batch_scale_for_root(root)
                per_piece_mm = ChatDrawingBomQuantitySemanticsService.per_piece_length_mm(
                    quantity=cable_qty,
                    unit=unit,
                    batch_scale=batch_scale,
                    item=cable_child,
                )

                if per_piece_mm is not None:
                    return per_piece_mm

            if unit in {"", "MM"} or unit not in cable_units:
                return cable_qty

        return pa_mm

    @classmethod
    def _product_description_length_mm(cls, root: dict) -> float | None:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        description = str(product.get("description") or "").strip().upper()

        if not description:
            structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

            for item in structure.get("items") or []:
                if not isinstance(item, dict):
                    continue

                item_type = str(item.get("type") or "").strip().upper()

                if item_type == "PA":
                    description = str(item.get("description") or "").strip().upper()
                    break

        if not description:
            return None

        match = ChatDrawingPatternsService.compile_validation(
            "productDescriptionLengthMm"
        ).search(description)

        if not match:
            return None

        return ChatDrawingToleranceService.parse_mm(match.group(1))

    @classmethod
    def _product_description_declares_length(cls, root: dict) -> bool:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        description = str(product.get("description") or "").strip().upper()

        if not description:
            return False

        return bool(
            ChatDrawingPatternsService.compile_validation(
                "productDescriptionLengthMm"
            ).search(description)
        )

    @classmethod
    def _resolve_cable_child(
        cls,
        item: dict,
    ) -> tuple[str | None, float | None, str | None, dict[str, Any] | None]:
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
            return None, None, None, None

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
            selected if isinstance(selected, dict) else None,
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
