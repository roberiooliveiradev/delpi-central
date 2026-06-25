"""Correção textual com leitura e atualização da lousa (canvas)."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_canvas_content_service import ChatCanvasOpenPayload
from app.application.services.chat_text_correction_answer_guard_service import (
    ChatTextCorrectionAnswerGuardService,
)
from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)


class ChatTextCorrectionCanvasService:
    @classmethod
    def load_active_canvas(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[str, str, str | None]:
        from app.domain.services.chat_canvas_history_service import ChatCanvasHistoryService

        return ChatCanvasHistoryService.find_active_canvas(previous_messages)

    @classmethod
    def _canvas_enabled(cls, workspace_context: dict | None) -> bool:
        agent = (workspace_context or {}).get("agent") or {}
        capabilities = agent.get("capabilities") or {}

        return capabilities.get("canvas") is not False

    @classmethod
    def should_update_canvas(cls, message: str | None) -> bool:
        return ChatTextCorrectionIntentService.is_canvas_text_correction(message)

    @classmethod
    def resolve_canvas_open_after_correction(
        cls,
        *,
        message: str | None,
        answer: str | None,
        previous_messages: list[Any] | None,
        workspace_context: dict | None = None,
    ) -> ChatCanvasOpenPayload | None:
        if not cls.should_update_canvas(message):
            return None

        if not cls._canvas_enabled(workspace_context):
            return None

        base_markdown, base_title, source_message_id = cls.load_active_canvas(
            previous_messages
        )

        if not base_markdown.strip():
            return None

        corrected = ChatTextCorrectionAnswerGuardService.extract_corrected_body(
            answer,
            message=message,
            workspace_context=workspace_context,
        )

        if not corrected or not corrected.strip():
            return None

        title = (base_title or "").strip() or "Texto corrigido"

        return ChatCanvasOpenPayload(
            title=title,
            markdown=corrected.strip(),
            source_message_id=source_message_id,
        )

    @classmethod
    def append_canvas_update_note(cls, answer: str, *, title: str) -> str:
        note = f"Atualizei a lousa «{title}» com a versão corrigida."

        if note.lower() in (answer or "").lower():
            return answer

        body = (answer or "").rstrip()

        return f"{body}\n\n{note}" if body else note
