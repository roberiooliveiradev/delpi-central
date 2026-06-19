"""Compara quantidades BOM PDF × SG1010 — tolerância declarada em validationRules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_structure_index_service import (
    ChatDrawingStructureIndexService,
)
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class BomQuantityMismatch:
    code: str
    pdf_quantity: float
    api_quantity: float


class ChatDrawingBomQuantityValidationService:
    @classmethod
    def compare(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> tuple[BomQuantityMismatch, ...]:
        api_quantities = cls.collect_api_quantities(root, product_code)
        pdf_quantities = cls.collect_pdf_quantities(pdf_extract)
        mismatches: list[BomQuantityMismatch] = []

        for code, api_qty in sorted(api_quantities.items()):
            pdf_qty = pdf_quantities.get(code)

            if pdf_qty is None:
                continue

            within = ChatDrawingToleranceService.lengths_within_tolerance(
                pdf_qty,
                api_qty,
                ratio=ChatDrawingPatternsService.quantity_tolerance_ratio(),
            )

            if within is False:
                mismatches.append(
                    BomQuantityMismatch(
                        code=code,
                        pdf_quantity=pdf_qty,
                        api_quantity=api_qty,
                    )
                )

        return tuple(mismatches)

    @classmethod
    def build_check_items(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> list[dict[str, Any]]:
        api_quantities = cls.collect_api_quantities(root, product_code)
        pdf_quantities = cls.collect_pdf_quantities(pdf_extract)
        mismatches = cls.compare(
            root=root,
            pdf_extract=pdf_extract,
            product_code=product_code,
        )
        content = ChatDrawingValidationContentService
        items: list[dict[str, Any]] = []

        for mismatch in mismatches[:6]:
            items.append(
                content.item_from_template(
                    "bom_quantity_mismatch",
                    status="critical_error",
                    pdf_evidence=content.evidence_format(
                        "bomQuantityPdf",
                        quantity=str(mismatch.pdf_quantity),
                    ),
                    api_evidence=content.evidence_format(
                        "bomQuantityApi",
                        quantity=str(mismatch.api_quantity),
                    ),
                    item_values={"code": mismatch.code},
                )
            )

        compared = {
            code for code in api_quantities if code in pdf_quantities
        }

        if compared and not mismatches:
            items.append(
                content.item_from_template(
                    "bom_quantity_ok",
                    status="ok",
                    pdf_evidence=content.evidence_format(
                        "codeCount",
                        count=str(len(compared)),
                    ),
                    api_evidence=content.evidence("linked"),
                )
            )

        return items

    @classmethod
    def collect_api_quantities(cls, root: dict, product_code: str) -> dict[str, float]:
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        quantities: dict[str, float] = {}

        for row in ChatDrawingStructureIndexService.flatten_items(structure):
            if not row.code or row.code == root_code:
                continue

            if row.depth != ChatDrawingPatternsService.structure_root_depth():
                continue

            quantity = cls._quantity_for_code(structure, row.code)

            if quantity is not None:
                quantities[row.code] = quantity

        return quantities

    @classmethod
    def collect_pdf_quantities(cls, pdf_extract: dict) -> dict[str, float]:
        quantities: dict[str, float] = {}

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )
            quantity = ChatDrawingToleranceService.parse_mm(row.get("quantity"))

            if code and quantity is not None:
                quantities[code] = quantity

        return quantities

    @classmethod
    def _quantity_for_code(cls, structure: dict, code: str) -> float | None:
        for item in cls._walk_structure_dicts(structure):
            item_code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("code") or "")
            )

            if item_code == code:
                return ChatDrawingToleranceService.parse_mm(item.get("quantity"))

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
