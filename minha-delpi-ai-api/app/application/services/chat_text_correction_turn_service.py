"""Helpers de turno para correção textual (prompt + pós-processamento)."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_text_correction_answer_guard_service import (
    ChatTextCorrectionAnswerGuardService,
)
from app.application.services.chat_text_correction_follow_up_service import (
    ChatTextCorrectionFollowUpService,
)
from app.application.services.chat_text_correction_canvas_service import (
    ChatTextCorrectionCanvasService,
)
from app.application.services.chat_text_correction_prompt_supplement_service import (
    ChatTextCorrectionPromptSupplementService,
)
from app.application.services.chat_canvas_content_service import ChatCanvasOpenPayload


class ChatTextCorrectionTurnService:
    @classmethod
    def build_prompt_supplement(
        cls,
        *,
        message: str | None,
        text_correction_mode: bool,
        text_correction_subtype: str | None,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
    ) -> str | None:
        if not text_correction_mode:
            return None

        block = ChatTextCorrectionPromptSupplementService.build(
            message=message,
            text_correction_subtype=text_correction_subtype,
            workspace_context=workspace_context,
            previous_messages=previous_messages,
        )

        return block or None

    @classmethod
    def resolve_canvas_open_after_correction(
        cls,
        *,
        message: str | None,
        answer: str | None,
        previous_messages: list | None,
        workspace_context: dict | None,
    ) -> ChatCanvasOpenPayload | None:
        return ChatTextCorrectionCanvasService.resolve_canvas_open_after_correction(
            message=message,
            answer=answer,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
        )

    @classmethod
    def apply_canvas_update_to_answer(
        cls,
        answer: str,
        *,
        canvas_payload: ChatCanvasOpenPayload | None,
    ) -> str:
        if not canvas_payload:
            return answer

        return ChatTextCorrectionCanvasService.append_canvas_update_note(
            answer,
            title=canvas_payload.title,
        )

    @classmethod
    def finalize_answer(
        cls,
        answer: str,
        *,
        message: str | None,
        workspace_context: dict | None,
    ) -> tuple[str, dict[str, Any] | None]:
        return ChatTextCorrectionAnswerGuardService.apply(
            answer,
            message=message,
            workspace_context=workspace_context,
        )

    @classmethod
    def attach_follow_up_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None,
        answer: str | None,
        workspace_context: dict | None,
        guard_meta: dict[str, Any] | None = None,
        canvas_updated: bool = False,
    ) -> None:
        ChatTextCorrectionFollowUpService.attach_to_assistant_metadata(
            metadata,
            message=message,
            answer=answer,
            workspace_context=workspace_context,
            guard_meta=guard_meta,
            canvas_updated=canvas_updated,
        )

        if canvas_updated:
            metadata["textCorrectionCanvasUpdate"] = {"applied": True}
