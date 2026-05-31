"""Metadata de turnos mistos (dados + texto) — Playbook 03 Fase 5."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


class ChatTextTaskMixedTurnService:
    @classmethod
    def build_snapshot(
        cls,
        *,
        message: str | None,
        pipeline_stages: list[str] | None = None,
        tool_context: dict | None = None,
    ) -> dict[str, Any] | None:
        if not ChatTextTaskIntentService.is_mixed_text_and_operational(message):
            return None

        stages = list(pipeline_stages or [])
        draft = (tool_context or {}).get("operationalEmailDraft")
        category = ChatTextTaskIntentService.classify(message)

        return {
            "operational": True,
            "textCategory": category,
            "draftAttached": isinstance(draft, dict) and bool(draft.get("text")),
            "stages": [s for s in stages if s in {"text_task_mixed", "email_operational", "direct_answer"}],
            "source": "operational_email_draft" if draft else "pending",
        }

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None,
        pipeline_stages: list[str] | None = None,
        tool_context: dict | None = None,
    ) -> None:
        snapshot = cls.build_snapshot(
            message=message,
            pipeline_stages=pipeline_stages,
            tool_context=tool_context,
        )

        if snapshot:
            metadata["textTaskMixed"] = snapshot
