"""Avisos de vigência BOM (G1_INI/G1_FIM) e desalinhamento revisão PDF × estrutura."""

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
                        columns=str(bom_validity.get("validityColumns") or "G1_INI,G1_FIM"),
                    ),
                )
            )

        pdf_revision = cls._normalize_revision_number(
            str(pdf_extract.get("internalRevision") or pdf_extract.get("revision") or "")
        )
        api_revision = cls._normalize_revision_number(
            str(product.get("current_revision") or "")
        )

        if (
            pdf_revision
            and api_revision
            and int(pdf_revision) < int(api_revision)
        ):
            items.append(
                content.item_from_template(
                    "structure_bom_validity_revision_lag",
                    status="pending",
                    pdf_evidence=content.evidence_format(
                        "revisionInternalTable",
                        revision=pdf_revision,
                    ),
                    api_evidence=content.evidence_format(
                        "revisionApiCurrent",
                        revision=api_revision,
                    ),
                )
            )

        return items

    @classmethod
    def _normalize_revision_number(cls, raw: str) -> str:
        value = str(raw or "").strip()

        if not value:
            return ""

        digits = "".join(char for char in value if char.isdigit())

        if not digits:
            return ""

        try:
            return str(int(digits)).zfill(2)
        except ValueError:
            return digits[-2:].zfill(2)
