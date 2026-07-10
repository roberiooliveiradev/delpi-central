"""Aplicação determinística de overrides humanos no checklist de desenho."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from app.domain.services.chat_drawing_report_adjustment_target_service import (
    ChatDrawingReportAdjustmentTargetService,
)
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

_ALLOWED_OVERRIDE_STATUS = frozenset({"ok", "not_applicable"})


class ChatDrawingReportAdjustmentService:
    @classmethod
    def load_overrides(cls, previous_messages: list | None) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}

        for item in previous_messages or []:
            if not isinstance(item, dict):
                continue

            if str(item.get("role") or "").strip().lower() != "assistant":
                continue

            metadata = item.get("metadata")

            if not isinstance(metadata, dict):
                continue

            candidates: list[Any] = []

            if isinstance(metadata.get("drawingAnalysisOverrides"), list):
                candidates.extend(metadata.get("drawingAnalysisOverrides") or [])

            drawing = metadata.get("drawingAnalysis")

            if isinstance(drawing, dict) and isinstance(
                drawing.get("drawingAnalysisOverrides"),
                list,
            ):
                candidates.extend(drawing.get("drawingAnalysisOverrides") or [])

            for override in candidates:
                if not isinstance(override, dict):
                    continue

                template_key = str(override.get("templateKey") or "").strip()

                if template_key:
                    merged[template_key] = override

        return list(merged.values())

    @classmethod
    def build_override(
        cls,
        *,
        template_key: str,
        analysis: dict[str, Any],
        source_message_id: str | None = None,
    ) -> dict[str, Any]:
        item = ChatDrawingReportAdjustmentTargetService.item_for_template_key(
            template_key,
            analysis,
        )
        item_label = str((item or {}).get("item") or template_key)
        reviewed_at = datetime.now(timezone.utc).isoformat()
        date_label = datetime.now(timezone.utc).strftime("%d/%m/%Y")

        return {
            "templateKey": template_key,
            "item": item_label,
            "section": str((item or {}).get("section") or ""),
            "previousStatus": str((item or {}).get("status") or ""),
            "status": "ok",
            "reason": ChatDrawingValidationContentService.format(
                "manualReview",
                "defaultReason",
            ),
            "pdfEvidenceOverride": ChatDrawingValidationContentService.format(
                "manualReview",
                "evidenceTemplate",
                date=date_label,
            ),
            "sourceMessageId": str(source_message_id or ""),
            "reviewedAt": reviewed_at,
            "reviewedBy": "user",
        }

    @classmethod
    def apply_overrides(
        cls,
        analysis: dict[str, Any],
        overrides: list[dict[str, Any]],
    ) -> dict[str, Any]:
        merged = copy.deepcopy(analysis)
        items = list(merged.get("items") or [])

        for override in overrides:
            if not isinstance(override, dict):
                continue

            template_key = str(override.get("templateKey") or "").strip()
            new_status = str(override.get("status") or "ok").strip()

            if new_status not in _ALLOWED_OVERRIDE_STATUS:
                continue

            for item in items:
                if str(item.get("templateKey") or "").strip() != template_key:
                    continue

                item["status"] = new_status
                evidence = str(override.get("pdfEvidenceOverride") or "").strip()

                if evidence:
                    item["pdfEvidence"] = evidence

                item["manualReview"] = True
                break

        merged["items"] = items
        merged["drawingAnalysisOverrides"] = list(overrides)
        return ChatDrawingValidationOrchestrationService.reconcile_analysis_summary(merged)

    @classmethod
    def merge_override_lists(
        cls,
        existing: list[dict[str, Any]],
        new_override: dict[str, Any],
    ) -> list[dict[str, Any]]:
        template_key = str(new_override.get("templateKey") or "").strip()
        merged = [
            item
            for item in existing
            if str(item.get("templateKey") or "").strip() != template_key
        ]
        merged.append(new_override)
        return merged
