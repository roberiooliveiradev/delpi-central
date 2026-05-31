"""Lousa para tarefas textuais com histórico de versões — Playbook 03 Fase 3/6."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_canvas_content_service import (
    ChatCanvasContentService,
    ChatCanvasOpenPayload,
)
from app.application.services.chat_text_correction_answer_guard_service import (
    ChatTextCorrectionAnswerGuardService,
)
from app.application.services.chat_text_correction_canvas_service import (
    ChatTextCorrectionCanvasService,
)
from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_task_service import ChatTextTaskService


class ChatTextTaskCanvasService:
    @classmethod
    def should_update_canvas(cls, message: str | None) -> bool:
        if ChatTextCorrectionIntentService.is_canvas_text_correction(message):
            return True

        ctx = ChatTextTaskService.classify(message)

        return ctx.get("source") == "canvas"

    @classmethod
    def resolve_canvas_open_after_text_task(
        cls,
        *,
        message: str | None,
        answer: str | None,
        previous_messages: list[Any] | None,
        workspace_context: dict | None = None,
    ) -> ChatCanvasOpenPayload | None:
        if not cls.should_update_canvas(message):
            return None

        if ChatTextCorrectionIntentService.is_text_correction(message):
            return ChatTextCorrectionCanvasService.resolve_canvas_open_after_correction(
                message=message,
                answer=answer,
                previous_messages=previous_messages,
                workspace_context=workspace_context,
            )

        if not ChatTextCorrectionCanvasService._canvas_enabled(workspace_context):
            return None

        base_markdown, base_title, source_message_id = ChatTextCorrectionCanvasService.load_active_canvas(
            previous_messages
        )

        if not base_markdown.strip():
            return None

        body = (answer or "").strip()

        if not body:
            return None

        title = (base_title or "").strip() or "Texto na lousa"

        return ChatCanvasOpenPayload(
            title=title,
            markdown=body,
            source_message_id=source_message_id,
        )

    @classmethod
    def append_canvas_update_note(
        cls,
        answer: str,
        *,
        title: str,
    ) -> str:
        return ChatTextCorrectionCanvasService.append_canvas_update_note(answer, title=title)

    @classmethod
    def attach_version_history(
        cls,
        metadata: dict,
        *,
        previous_messages: list[Any] | None,
        new_markdown: str,
        title: str,
    ) -> None:
        base_markdown, _, _ = ChatTextCorrectionCanvasService.load_active_canvas(previous_messages)
        versions: list[dict[str, Any]] = []

        for msg in reversed(previous_messages or []):
            msg_meta = getattr(msg, "metadata", None) or (msg.get("metadata") if isinstance(msg, dict) else None)

            if not isinstance(msg_meta, dict):
                continue

            prior = msg_meta.get("textCanvasVersions")

            if isinstance(prior, list) and prior:
                versions = list(prior)
                break

        if base_markdown.strip():
            versions.append(
                {
                    "version": len(versions) + 1,
                    "title": title,
                    "markdown": base_markdown.strip()[:8000],
                    "role": "previous",
                }
            )

        versions.append(
            {
                "version": len(versions) + 1,
                "title": title,
                "markdown": new_markdown.strip()[:8000],
                "role": "current",
            }
        )

        metadata["textCanvasVersions"] = versions[-6:]
        metadata["textCanvasUpdated"] = True

    @classmethod
    def extract_body_for_canvas(
        cls,
        answer: str | None,
        *,
        message: str | None,
        workspace_context: dict | None,
    ) -> str | None:
        if ChatTextCorrectionIntentService.is_text_correction(message):
            return ChatTextCorrectionAnswerGuardService.extract_corrected_body(
                answer,
                message=message,
                workspace_context=workspace_context,
            )

        return (answer or "").strip() or None
