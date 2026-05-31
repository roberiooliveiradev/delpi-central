"""Métricas leves de tarefas textuais — Playbook 03 §29."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_text_task_service import ChatTextTaskService


class ChatTextTaskMetricsService:
    @classmethod
    def build_snapshot(
        cls,
        *,
        message: str | None,
        workspace_context: dict | None = None,
    ) -> dict[str, Any] | None:
        if not (
            ChatTextTaskService.is_text_task(message)
            or (workspace_context or {}).get("textTaskMode")
        ):
            return None

        ctx = ChatTextTaskService.classify(message)

        return {
            "type": ctx.get("type"),
            "subtype": ctx.get("subtype"),
            "tone": ctx.get("tone"),
            "deliverFinalOnly": bool(ctx.get("deliverFinalOnly")),
            "source": ctx.get("source"),
        }

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None,
        workspace_context: dict | None = None,
    ) -> None:
        snapshot = cls.build_snapshot(message=message, workspace_context=workspace_context)

        if snapshot:
            metadata["textTaskMetrics"] = snapshot
