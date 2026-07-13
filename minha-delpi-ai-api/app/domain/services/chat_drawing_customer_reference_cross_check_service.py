"""Cruzamento REF. do cliente no PDF × B1_REFEREN (api-delpi)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)


class ChatDrawingCustomerReferenceCrossCheckService:
    _STATUS_OK = "ok"
    _STATUS_PENDING = "pending"
    _STATUS_CRITICAL = "critical_error"

    @classmethod
    def build_check_item(
        cls,
        *,
        pdf_reference: str,
        api_reference: str,
    ) -> dict[str, Any] | None:
        pdf_norm = cls.normalize(pdf_reference)
        api_norm = cls.normalize(api_reference)
        content = ChatDrawingValidationContentService

        if not pdf_norm and not api_norm:
            return None

        if pdf_norm and api_norm and pdf_norm == api_norm:
            return content.item_from_template(
                "customer_reference_ok",
                status=cls._STATUS_OK,
                pdf_evidence=str(pdf_reference).strip() or pdf_norm,
                api_evidence=str(api_reference).strip() or api_norm,
            )

        if pdf_norm and api_norm:
            return content.item_from_template(
                "customer_reference_mismatch",
                status=cls._STATUS_CRITICAL,
                pdf_evidence=str(pdf_reference).strip() or pdf_norm,
                api_evidence=str(api_reference).strip() or api_norm,
            )

        if api_norm and not pdf_norm:
            return content.item_from_template(
                "customer_reference_pending_pdf",
                status=cls._STATUS_PENDING,
                pdf_evidence=content.evidence("dash"),
                api_evidence=str(api_reference).strip() or api_norm,
            )

        return content.item_from_template(
            "customer_reference_pending_api",
            status=cls._STATUS_PENDING,
            pdf_evidence=str(pdf_reference).strip() or pdf_norm,
            api_evidence=content.evidence("dash"),
        )

    @classmethod
    def normalize(cls, raw: str) -> str:
        value = str(raw or "").strip().upper()

        if not value:
            return ""

        return re.sub(r"[^A-Z0-9]", "", value)

    @classmethod
    def resolve_pdf_reference(cls, pdf_extract: dict[str, Any] | None) -> str:
        meta = pdf_extract if isinstance(pdf_extract, dict) else {}
        direct = str(meta.get("customerReference") or "").strip()

        if direct:
            return direct

        title_block = meta.get("titleBlock")

        if isinstance(title_block, dict):
            fields = title_block.get("fields")

            if isinstance(fields, dict):
                from_fields = str(fields.get("customerCode") or "").strip()

                if from_fields:
                    return from_fields

        return ""

    @classmethod
    def resolve_api_reference(cls, product: dict[str, Any] | None) -> str:
        row = product if isinstance(product, dict) else {}

        for key in ("customer_reference", "customerReference", "B1_REFEREN"):
            value = str(row.get(key) or "").strip()

            if value:
                return value

        return ""
