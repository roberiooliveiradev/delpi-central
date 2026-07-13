"""Avisos de vigência BOM (G1_INI/G1_FIM).

A revisão Delpi (B1_REVATU) não aparece no PDF — só no TOTVS —, portanto
não há aviso de «lag» revisão do desenho × cadastro.
"""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)


class ChatDrawingStructureValidityNoticeService:
    @classmethod
    def build_check_items(
        cls,
        *,
        product: dict,
        pdf_extract: dict,
        structure: dict,
    ) -> list[dict[str, Any]]:
        del product, pdf_extract  # revisão Delpi não vem do PDF
        items: list[dict[str, Any]] = []
        content = ChatDrawingValidationContentService
        bom_validity = (
            structure.get("bom_validity")
            if isinstance(structure.get("bom_validity"), dict)
            else {}
        )

        if str(bom_validity.get("filter") or "").strip().lower() == "current":
            items.append(
                content.item_from_template(
                    "structure_bom_validity_ok",
                    status="ok",
                    pdf_evidence=content.evidence("dash"),
                    api_evidence=content.evidence_format(
                        "structureBomValidityFilter",
                        columns=str(
                            bom_validity.get("validityColumns") or "G1_INI,G1_FIM"
                        ),
                    ),
                )
            )

        return items
