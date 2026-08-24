"""Chips de interatividade para enrich insight em modo Rápida."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)


class ChatGroundedEnrichInteractivityService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        tool_context: dict[str, Any] | None,
        response_mode: str | None,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        if ChatResponseModeService.normalize(response_mode) != "fast":
            return

        stage = cls._resolve_stage(tool_context)

        if stage != "grounded_enrich_insight":
            return

        suggestions = ChatTurnGroundingContentService.fast_enrich_insight_mode_suggestions()

        if suggestions:
            metadata["groundedEnrichModeSuggestions"] = suggestions

    @classmethod
    def _resolve_stage(cls, tool_context: dict[str, Any] | None) -> str:
        if not isinstance(tool_context, dict):
            return ""

        turn_grounding = tool_context.get("turnGrounding")

        if isinstance(turn_grounding, dict):
            return str(turn_grounding.get("stage") or "").strip()

        return str(tool_context.get("turnGroundingStage") or "").strip()
