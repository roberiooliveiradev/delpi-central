"""Apresentação do relatório de validação de desenho — consolidação e rótulos."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)


class ChatDrawingValidationPresentationService:
    @classmethod
    def status_label(cls, status: str) -> str:
        node = ChatDrawingValidationContentService.get_node(
            "statusPresentation",
            str(status or "").strip(),
        )

        if isinstance(node, dict) and node.get("label"):
            return str(node["label"])

        return str(status or "—")

    @classmethod
    def status_symbol(cls, status: str) -> str:
        node = ChatDrawingValidationContentService.get_node(
            "statusPresentation",
            str(status or "").strip(),
        )

        if isinstance(node, dict) and node.get("symbol"):
            return str(node["symbol"])

        return "—"

    @classmethod
    def status_display(cls, status: str) -> str:
        symbol = cls.status_symbol(status).strip()
        label = cls.status_label(status).strip()

        if symbol and symbol != "—":
            return f"{symbol} {label}"

        return label

    @classmethod
    def status_labels_map(cls) -> dict[str, str]:
        node = ChatDrawingValidationContentService.get_node("statusPresentation") or {}

        if not isinstance(node, dict):
            return {}

        return {
            str(key): str(value.get("label") or key)
            for key, value in node.items()
            if isinstance(value, dict)
        }

    @classmethod
    def divergence_statuses(cls) -> tuple[str, ...]:
        items = ChatDrawingValidationContentService.list_values(
            "presentation",
            "divergenceStatuses",
        )

        return tuple(str(item).strip() for item in items if str(item).strip())

    @classmethod
    def divergence_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        allowed = set(cls.divergence_statuses())

        return [
            item
            for item in items
            if isinstance(item, dict) and str(item.get("status") or "") in allowed
        ]

    @classmethod
    def nonconformity_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            item
            for item in items
            if isinstance(item, dict) and str(item.get("status") or "") != "ok"
        ]

    @classmethod
    def consolidate_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        consolidate_keys = {
            str(key).strip()
            for key in ChatDrawingValidationContentService.list_values(
                "presentation",
                "consolidateTemplateKeys",
            )
            if str(key).strip()
        }
        normalized = [item for item in items if isinstance(item, dict)]

        if not consolidate_keys:
            return normalized

        joiner = ChatDrawingValidationContentService.get(
            "presentation",
            "evidenceJoiner",
            default="; ",
        )
        consolidated_template = str(
            ChatDrawingValidationContentService.get(
                "presentation",
                "consolidatedTemplateKey",
                default="segment_lengths_consolidated",
            )
        ).strip()
        buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}

        for item in normalized:
            template_key = str(item.get("templateKey") or "").strip()
            section = str(item.get("section") or "")

            if template_key in consolidate_keys:
                buckets.setdefault((section, template_key), []).append(item)

        result: list[dict[str, Any]] = []
        emitted: set[tuple[str, str]] = set()

        for item in normalized:
            template_key = str(item.get("templateKey") or "").strip()
            section = str(item.get("section") or "")

            if template_key not in consolidate_keys:
                result.append(item)
                continue

            bucket_key = (section, template_key)

            if bucket_key in emitted:
                continue

            emitted.add(bucket_key)
            bucket_items = buckets.get(bucket_key) or []

            if len(bucket_items) <= 1:
                result.extend(bucket_items)
                continue

            pdf_values = [
                str(row.get("pdfEvidence") or "").strip()
                for row in bucket_items
                if str(row.get("pdfEvidence") or "").strip()
            ]
            api_values = [
                str(row.get("apiEvidence") or "").strip()
                for row in bucket_items
                if str(row.get("apiEvidence") or "").strip()
            ]

            result.append(
                ChatDrawingValidationContentService.item_from_template(
                    consolidated_template,
                    status=cls._worst_status(row.get("status") for row in bucket_items),
                    pdf_evidence=joiner.join(dict.fromkeys(pdf_values)),
                    api_evidence=joiner.join(dict.fromkeys(api_values)),
                )
            )

        return result

    @classmethod
    def _worst_status(cls, statuses: Any) -> str:
        ranking = {
            "critical_error": 4,
            "error": 3,
            "pending": 2,
            "ok": 1,
            "not_applicable": 0,
        }
        best = "pending"

        for status in statuses:
            key = str(status or "").strip()

            if ranking.get(key, 0) >= ranking.get(best, 0):
                best = key

        return best
