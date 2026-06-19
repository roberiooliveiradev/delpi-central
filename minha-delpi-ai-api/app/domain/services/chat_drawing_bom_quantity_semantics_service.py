"""Semântica PDF × SG1010 para quantidades BOM — milheiro (MI) e unidades distintas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_structure_index_service import (
    ChatDrawingStructureIndexService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class StructureQuantityRow:
    code: str
    quantity: float
    unit: str


@dataclass(frozen=True)
class PdfQuantityNormalization:
    comparable: bool
    pdf_value: float | None
    evidence_key: str
    evidence_values: dict[str, str]


class ChatDrawingBomQuantitySemanticsService:
    @classmethod
    def batch_scale_for_root(cls, root: dict) -> float:
        unit = cls._root_product_unit(root)

        if unit in cls._milheiro_batch_units():
            return cls._pieces_per_milheiro()

        return 1.0

    @classmethod
    def collect_structure_quantities(
        cls,
        root: dict,
        product_code: str,
    ) -> dict[str, StructureQuantityRow]:
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        quantities: dict[str, StructureQuantityRow] = {}

        for row in ChatDrawingStructureIndexService.flatten_items(structure):
            if not row.code or row.code == root_code:
                continue

            if row.depth != ChatDrawingPatternsService.structure_root_depth():
                continue

            item = cls._structure_item(structure, row.code)
            quantity = cls._parse_quantity(item.get("quantity") if item else None)

            if quantity is None:
                continue

            quantities[row.code] = StructureQuantityRow(
                code=row.code,
                quantity=quantity,
                unit=cls._item_unit(item or {}),
            )

        return quantities

    @classmethod
    def normalize_pdf_quantity(
        cls,
        *,
        pdf_quantity: float,
        api_row: StructureQuantityRow,
        root: dict,
        pdf_extract: dict,
    ) -> PdfQuantityNormalization:
        batch_scale = cls.batch_scale_for_root(root)
        api_unit = api_row.unit.upper()
        piece_units = ChatDrawingPatternsService.piece_count_units()
        cable_units = ChatDrawingPatternsService.cable_length_units()

        if ChatDrawingPatternsService.is_intermediate_family(api_row.code):
            return cls._normalize_intermediate_quantity(
                pdf_quantity=pdf_quantity,
                api_row=api_row,
                batch_scale=batch_scale,
            )

        if api_unit in piece_units:
            normalized = pdf_quantity * batch_scale

            if batch_scale > 1:
                return PdfQuantityNormalization(
                    comparable=True,
                    pdf_value=normalized,
                    evidence_key="bomQuantityPdfMilheiro",
                    evidence_values={
                        "quantity": cls._format_quantity(pdf_quantity),
                        "scale": cls._format_quantity(batch_scale),
                        "normalized": cls._format_quantity(normalized),
                    },
                )

            return PdfQuantityNormalization(
                comparable=True,
                pdf_value=pdf_quantity,
                evidence_key="bomQuantityPdf",
                evidence_values={"quantity": cls._format_quantity(pdf_quantity)},
            )

        if api_unit in cable_units:
            if not ChatDrawingBomQuantitySemanticsService.is_cable_material_code(
                api_row.code,
                cls._structure_item_description(root, api_row.code),
            ):
                return PdfQuantityNormalization(
                    comparable=False,
                    pdf_value=None,
                    evidence_key="bomQuantityPdf",
                    evidence_values={"quantity": cls._format_quantity(pdf_quantity)},
                )

            return cls._normalize_cable_length_quantity(
                pdf_quantity=pdf_quantity,
                api_row=api_row,
                root=root,
                pdf_extract=pdf_extract,
                batch_scale=batch_scale,
            )

        return PdfQuantityNormalization(
            comparable=True,
            pdf_value=pdf_quantity,
            evidence_key="bomQuantityPdf",
            evidence_values={"quantity": cls._format_quantity(pdf_quantity)},
        )

    @classmethod
    def _normalize_intermediate_quantity(
        cls,
        *,
        pdf_quantity: float,
        api_row: StructureQuantityRow,
        batch_scale: float,
    ) -> PdfQuantityNormalization:
        """PI/50xx — PDF qtd por chicote; MI na SG1010 é contagem de lote, não comprimento de cabo."""
        api_unit = api_row.unit.upper()
        piece_units = ChatDrawingPatternsService.piece_count_units()

        if api_unit in piece_units:
            normalized = pdf_quantity * batch_scale

            if batch_scale > 1:
                return PdfQuantityNormalization(
                    comparable=True,
                    pdf_value=normalized,
                    evidence_key="bomQuantityPdfMilheiro",
                    evidence_values={
                        "quantity": cls._format_quantity(pdf_quantity),
                        "scale": cls._format_quantity(batch_scale),
                        "normalized": cls._format_quantity(normalized),
                    },
                )

            return PdfQuantityNormalization(
                comparable=True,
                pdf_value=pdf_quantity,
                evidence_key="bomQuantityPdf",
                evidence_values={"quantity": cls._format_quantity(pdf_quantity)},
            )

        if api_unit in cls._milheiro_batch_units() or api_unit == "UN":
            return PdfQuantityNormalization(
                comparable=True,
                pdf_value=pdf_quantity,
                evidence_key="bomQuantityPdf",
                evidence_values={"quantity": cls._format_quantity(pdf_quantity)},
            )

        return PdfQuantityNormalization(
            comparable=False,
            pdf_value=None,
            evidence_key="bomQuantityPdf",
            evidence_values={"quantity": cls._format_quantity(pdf_quantity)},
        )

    @classmethod
    def _normalize_cable_length_quantity(
        cls,
        *,
        pdf_quantity: float,
        api_row: StructureQuantityRow,
        root: dict,
        pdf_extract: dict,
        batch_scale: float,
    ) -> PdfQuantityNormalization:
        max_piece_qty = ChatDrawingPatternsService.max_piece_count_quantity()

        if pdf_quantity > max_piece_qty:
            return PdfQuantityNormalization(
                comparable=False,
                pdf_value=None,
                evidence_key="bomQuantityPdf",
                evidence_values={"quantity": cls._format_quantity(pdf_quantity)},
            )

        length_mm = cls._resolve_drawing_cable_length_mm(
            code=api_row.code,
            root=root,
            pdf_extract=pdf_extract,
        )

        if length_mm is None:
            return PdfQuantityNormalization(
                comparable=False,
                pdf_value=None,
                evidence_key="bomQuantityPdf",
                evidence_values={"quantity": cls._format_quantity(pdf_quantity)},
            )

        length_m = length_mm / 1000.0
        normalized_mt = pdf_quantity * length_m * batch_scale

        return PdfQuantityNormalization(
            comparable=True,
            pdf_value=normalized_mt,
            evidence_key="bomQuantityPdfCableLength",
            evidence_values={
                "quantity": cls._format_quantity(pdf_quantity),
                "lengthMm": cls._format_quantity(length_mm),
                "normalized": cls._format_quantity(normalized_mt),
            },
        )

    @classmethod
    def _resolve_drawing_cable_length_mm(
        cls,
        *,
        code: str,
        root: dict,
        pdf_extract: dict,
    ) -> float | None:
        dimensions = pdf_extract.get("dimensions")

        if isinstance(dimensions, dict):
            total = cls._parse_quantity(dimensions.get("totalLengthMm"))

            if total is not None and total > 0:
                return total

            segments = dimensions.get("segmentLengthsMm")

            if isinstance(segments, list) and segments:
                parsed_segments = [
                    value
                    for value in (cls._parse_quantity(item) for item in segments)
                    if value is not None and value > 0
                ]

                if parsed_segments:
                    plausible = [
                        value
                        for value in parsed_segments
                        if value
                        <= ChatDrawingPatternsService.max_root_structure_quantity_mm()
                    ]

                    if plausible:
                        return max(plausible)

        item = cls._structure_item(
            root.get("structure") if isinstance(root.get("structure"), dict) else {},
            code,
        )

        if not item:
            return None

        quantity = cls._parse_quantity(item.get("quantity"))

        if quantity is None:
            return None

        return cls.per_piece_length_mm(
            quantity=quantity,
            unit=cls._item_unit(item) or "MT",
            batch_scale=cls.batch_scale_for_root(root),
        )

    @classmethod
    def _structure_item_description(cls, root: dict, code: str) -> str:
        item = cls._structure_item(
            root.get("structure") if isinstance(root.get("structure"), dict) else {},
            code,
        )

        if not item:
            return ""

        return str(item.get("description") or "")

    @classmethod
    def quantity_to_mm(cls, quantity: float, unit: str) -> float | None:
        normalized_unit = str(unit or "").strip().upper()

        if not normalized_unit:
            return None

        if normalized_unit in {"MT", "M"}:
            return quantity * 1000.0

        if normalized_unit == "MM":
            return quantity

        return None

    @classmethod
    def per_piece_length_mm(
        cls,
        *,
        quantity: float,
        unit: str,
        batch_scale: float,
    ) -> float | None:
        total_mm = cls.quantity_to_mm(quantity, unit)

        if total_mm is None or batch_scale <= 0:
            return None

        return total_mm / batch_scale

    @classmethod
    def is_cable_material_code(cls, code: str, description: str = "") -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code)
        upper_desc = str(description or "").upper()

        if normalized.startswith("104"):
            return True

        return "CABO" in upper_desc or "CABOS" in upper_desc

    @classmethod
    def _root_product_unit(cls, root: dict) -> str:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}

        for key in ("unit", "component_unit", "unidade"):
            value = str(product.get(key) or "").strip().upper()

            if value:
                return value

        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        items = structure.get("items") if isinstance(structure.get("items"), list) else []

        for item in items:
            if not isinstance(item, dict):
                continue

            unit = cls._item_unit(item)

            if unit:
                return unit

        return ""

    @classmethod
    def _item_unit(cls, item: dict[str, Any]) -> str:
        for key in ("unit", "component_unit", "unidade"):
            raw = item.get(key)

            if raw is None:
                continue

            value = str(raw).strip().upper()

            if value:
                return value

        return ""

    @classmethod
    def _structure_item(cls, structure: dict, code: str) -> dict[str, Any] | None:
        target = ChatProductQueryIntentService.normalize_product_code(code)

        for item in cls._walk_structure_dicts(structure):
            item_code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("code") or "")
            )

            if item_code == target:
                return item

        return None

    @classmethod
    def _walk_structure_dicts(cls, structure: dict) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        def walk(items: list[Any]) -> None:
            for item in items:
                if not isinstance(item, dict):
                    continue

                rows.append(item)

                child_components = item.get("components")

                if isinstance(child_components, list):
                    walk(child_components)

        walk(structure.get("items") or [])

        return rows

    @classmethod
    def _milheiro_batch_units(cls) -> frozenset[str]:
        items = ChatDrawingPatternsService.bom_quantity_semantics_rule(
            "milheiroBatchUnits",
            ["MI"],
        )
        return frozenset(str(item).strip().upper() for item in items if str(item).strip())

    @classmethod
    def _pieces_per_milheiro(cls) -> float:
        return ChatDrawingPatternsService.bom_quantity_semantics_float(
            "piecesPerMilheiro",
            1000.0,
        )

    @classmethod
    def _parse_quantity(cls, raw: Any) -> float | None:
        if raw is None:
            return None

        try:
            value = float(str(raw).replace(",", ".").strip())
        except (TypeError, ValueError):
            return None

        return value if value >= 0 else None

    @classmethod
    def _format_quantity(cls, value: float) -> str:
        if float(value).is_integer():
            return str(int(value))

        return str(value)
