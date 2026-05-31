"""Helpers de turno para correção textual (prompt + pós-processamento)."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_text_correction_answer_guard_service import (
    ChatTextCorrectionAnswerGuardService,
)
from app.application.services.chat_text_correction_follow_up_service import (
    ChatTextCorrectionFollowUpService,
)
from app.application.services.chat_text_correction_prompt_supplement_service import (
    ChatTextCorrectionPromptSupplementService,
)


class ChatTextCorrectionTurnService:
    @classmethod
    def build_prompt_supplement(
        cls,
        *,
        message: str | None,
        text_correction_mode: bool,
        text_correction_subtype: str | None,
    ) -> str | None:
        if not text_correction_mode:
            return None

        block = ChatTextCorrectionPromptSupplementService.build(
            message=message,
            text_correction_subtype=text_correction_subtype,
        )

        return block or None

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
    ) -> None:
        ChatTextCorrectionFollowUpService.attach_to_assistant_metadata(
            metadata,
            message=message,
            answer=answer,
            workspace_context=workspace_context,
            guard_meta=guard_meta,
        )
