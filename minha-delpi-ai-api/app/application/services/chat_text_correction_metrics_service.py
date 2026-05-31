"""Métricas leves de correção textual (metadata / adminDebug)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_correction_preference_service import (
    ChatTextCorrectionPreferenceService,
)
from app.domain.services.chat_text_correction_quality_validator import (
    ChatTextCorrectionQualityValidator,
)


class ChatTextCorrectionMetricsService:
    @classmethod
    def build_snapshot(
        cls,
        *,
        message: str | None,
        answer: str | None = None,
        workspace_context: dict | None = None,
        guard_meta: dict[str, Any] | None = None,
        follow_up_count: int = 0,
        canvas_updated: bool = False,
    ) -> dict[str, Any] | None:
        if not (
            ChatTextCorrectionIntentService.is_text_correction(message)
            or (workspace_context or {}).get("textCorrectionMode")
        ):
            return None

        working_memory = (workspace_context or {}).get("workingMemory") or {}
        ctx = ChatTextCorrectionIntentService.extract_context(
            message,
            working_memory=working_memory,
        )
        prefs = ChatTextCorrectionPreferenceService.detect(
            message,
            working_memory=working_memory,
        )
        quality = (guard_meta or {}).get("textCorrectionGuard", {}).get("quality")

        if not isinstance(quality, dict):
            quality = ChatTextCorrectionQualityValidator.validate(
                answer,
                user_message=message,
                subtype=ctx.get("subtype"),
                preserved_codes=ctx.get("preservedCodes"),
            )

        return {
            "subtype": ctx.get("subtype"),
            "source": ctx.get("source"),
            "preferenceCount": len(prefs),
            "preferences": list(prefs.keys()),
            "qualityPassed": bool(quality.get("passed")),
            "qualityCheckCount": len(quality.get("checks") or []),
            "hasSourceText": bool(ctx.get("sourceText")),
            "preservedCodeCount": len(ctx.get("preservedCodes") or []),
            "deliverFinalOnly": bool(ctx.get("deliverFinalOnly")),
            "explainChanges": bool(ctx.get("explainChanges")),
            "followUpChipCount": follow_up_count,
            "canvasUpdated": bool(canvas_updated),
            "canvasSource": ctx.get("source") == "canvas",
        }

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None = None,
        answer: str | None = None,
        workspace_context: dict | None = None,
        guard_meta: dict[str, Any] | None = None,
        follow_up_count: int = 0,
        canvas_updated: bool = False,
    ) -> None:
        snapshot = cls.build_snapshot(
            message=message,
            answer=answer,
            workspace_context=workspace_context,
            guard_meta=guard_meta,
            follow_up_count=follow_up_count,
            canvas_updated=canvas_updated,
        )

        if snapshot:
            metadata["textCorrectionMetrics"] = snapshot
