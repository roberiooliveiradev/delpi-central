"""Compara quantidades BOM PDF × SG1010 — tolerância declarada em validationRules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_bom_quantity_assertiveness_service import (
    ChatDrawingBomQuantityAssertivenessService,
)
from app.domain.services.chat_drawing_bom_quantity_semantics_service import (
    ChatDrawingBomQuantitySemanticsService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)


@dataclass(frozen=True)
class BomQuantityMismatch:
    code: str
    pdf_quantity: float
    api_quantity: float
    pdf_evidence_key: str
    pdf_evidence_values: dict[str, str]
    trusted: bool = True


@dataclass(frozen=True)
class BomQuantityPending:
    code: str
    pdf_quantity: float
    pdf_evidence_key: str
    pdf_evidence_values: dict[str, str]


class ChatDrawingBomQuantityValidationService:
    @classmethod
    def compare(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> tuple[BomQuantityMismatch, ...]:
        api_quantities = ChatDrawingBomQuantitySemanticsService.collect_structure_quantities(
            root,
            product_code,
        )
        evidences = ChatDrawingBomQuantityAssertivenessService.collect_evidences(
            root=root,
            pdf_extract=pdf_extract,
            product_code=product_code,
        )
        mismatches: list[BomQuantityMismatch] = []

        for code, api_row in sorted(api_quantities.items()):
            evidence = evidences.get(code)

            if evidence is None or not evidence.trusted:
                continue

            pdf_qty = evidence.quantity
            normalization = ChatDrawingBomQuantitySemanticsService.normalize_pdf_quantity(
                pdf_quantity=pdf_qty,
                api_row=api_row,
                root=root,
                pdf_extract=pdf_extract,
            )

            if not normalization.comparable or normalization.pdf_value is None:
                continue

            within = ChatDrawingToleranceService.lengths_within_tolerance(
                normalization.pdf_value,
                api_row.quantity,
                ratio=ChatDrawingPatternsService.quantity_tolerance_ratio(),
            )

            if within is False:
                mismatches.append(
                    BomQuantityMismatch(
                        code=code,
                        pdf_quantity=normalization.pdf_value,
                        api_quantity=api_row.quantity,
                        pdf_evidence_key=normalization.evidence_key,
                        pdf_evidence_values=normalization.evidence_values,
                        trusted=True,
                    )
                )

        return tuple(mismatches)

    @classmethod
    def collect_pending(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> tuple[BomQuantityPending, ...]:
        api_quantities = ChatDrawingBomQuantitySemanticsService.collect_structure_quantities(
            root,
            product_code,
        )
        evidences = ChatDrawingBomQuantityAssertivenessService.collect_evidences(
            root=root,
            pdf_extract=pdf_extract,
            product_code=product_code,
        )
        pending: list[BomQuantityPending] = []

        for code, api_row in sorted(api_quantities.items()):
            evidence = evidences.get(code)

            if evidence is None:
                continue

            if not evidence.trusted and evidence.reason in (
                ChatDrawingPatternsService.bom_quantity_skip_pending_reasons()
            ):
                continue

            if evidence.trusted:
                normalization = ChatDrawingBomQuantitySemanticsService.normalize_pdf_quantity(
                    pdf_quantity=evidence.quantity,
                    api_row=api_row,
                    root=root,
                    pdf_extract=pdf_extract,
                )

                if normalization.comparable:
                    continue

                pending.append(
                    BomQuantityPending(
                        code=code,
                        pdf_quantity=evidence.quantity,
                        pdf_evidence_key=normalization.evidence_key,
                        pdf_evidence_values=normalization.evidence_values,
                    )
                )
                continue

            normalization = ChatDrawingBomQuantitySemanticsService.normalize_pdf_quantity(
                pdf_quantity=evidence.quantity,
                api_row=api_row,
                root=root,
                pdf_extract=pdf_extract,
            )
            pending.append(
                BomQuantityPending(
                    code=code,
                    pdf_quantity=evidence.quantity,
                    pdf_evidence_key=normalization.evidence_key,
                    pdf_evidence_values=normalization.evidence_values,
                )
            )

        return tuple(pending)

    @classmethod
    def build_check_items(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> list[dict[str, Any]]:
        api_quantities = ChatDrawingBomQuantitySemanticsService.collect_structure_quantities(
            root,
            product_code,
        )
        evidences = ChatDrawingBomQuantityAssertivenessService.collect_evidences(
            root=root,
            pdf_extract=pdf_extract,
            product_code=product_code,
        )
        mismatches = cls.compare(
            root=root,
            pdf_extract=pdf_extract,
            product_code=product_code,
        )
        pending = cls.collect_pending(
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
                    status=ChatDrawingBomQuantityAssertivenessService.mismatch_status(
                        trusted=mismatch.trusted,
                        pdf_extract=pdf_extract,
                        code=mismatch.code,
                    ),
                    pdf_evidence=content.evidence_format(
                        mismatch.pdf_evidence_key,
                        **mismatch.pdf_evidence_values,
                    ),
                    api_evidence=content.evidence_format(
                        "bomQuantityApi",
                        quantity=str(mismatch.api_quantity),
                    ),
                    item_values={"code": mismatch.code},
                )
            )

        pending_codes = {row.code for row in pending}

        for row in pending[:4]:
            items.append(
                content.item_from_template(
                    "bom_quantity_pending",
                    status=ChatDrawingPatternsService.bom_quantity_pending_status(),
                    pdf_evidence=content.evidence_format(
                        row.pdf_evidence_key,
                        **row.pdf_evidence_values,
                    ),
                    api_evidence=content.evidence_format(
                        "bomQuantityApi",
                        quantity=str(api_quantities[row.code].quantity),
                    ),
                    item_values={"code": row.code},
                )
            )

        compared = {
            code
            for code, evidence in evidences.items()
            if code in api_quantities
            and evidence.trusted
            and code not in pending_codes
            and not any(item.code == code for item in mismatches)
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
    def collect_pdf_quantities(cls, pdf_extract: dict) -> dict[str, float]:
        quantities: dict[str, float] = {}

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            from app.domain.services.chat_product_query_intent_service import (
                ChatProductQueryIntentService,
            )

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )
            quantity = ChatDrawingToleranceService.parse_mm(row.get("quantity"))

            if code and quantity is not None:
                quantities[code] = quantity

        return quantities
