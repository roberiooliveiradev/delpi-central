"""Catálogo JSON `drawing_validation` — itens de checklist e evidências."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "drawing_validation"


class ChatDrawingValidationContentService:
    @classmethod
    def get(cls, *path: str, default: str = "") -> str:
        return ChatAssistantContentService.get(_BUNDLE, *path, default=default)

    @classmethod
    def format(cls, *path: str, default: str = "", **values: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            *path,
            default=default,
            **values,
        )

    @classmethod
    def evidence(cls, key: str) -> str:
        return cls.get("evidence", key)

    @classmethod
    def evidence_format(cls, key: str, **values: str) -> str:
        return cls.format("evidenceFormats", key, **values)

    @classmethod
    def decape_side(cls, side: str) -> str:
        return cls.get("decapeSides", side, default=side)

    @classmethod
    def item_from_template(
        cls,
        template_key: str,
        *,
        status: str,
        pdf_evidence: str,
        api_evidence: str,
        recommendation: str | None = None,
        recommendation_field: str = "recommendation",
        item_values: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        template = (
            ChatAssistantContentService.get_node(
                _BUNDLE,
                "itemTemplates",
                template_key,
            )
            or {}
        )

        if recommendation is None:
            recommendation = str(
                template.get(recommendation_field)
                or template.get("recommendation")
                or cls.evidence("dash")
            )

        item_label = str(template.get("item") or cls.evidence("dash"))

        if item_values:
            item_label = cls.format(
                "itemTemplates",
                template_key,
                "item",
                default=item_label,
                **item_values,
            )

        return {
            "section": str(template.get("section") or cls.evidence("dash")),
            "item": item_label,
            "status": status,
            "pdfEvidence": pdf_evidence,
            "apiEvidence": api_evidence,
            "rule": str(template.get("rule") or cls.evidence("dash")),
            "recommendation": recommendation,
        }
