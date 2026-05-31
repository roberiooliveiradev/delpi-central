"""Helpers de turno para escrita de e-mail (prompt + pós-processamento)."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_email_follow_up_service import ChatEmailFollowUpService
from app.application.services.chat_email_prompt_supplement_service import (
    ChatEmailPromptSupplementService,
)
from app.application.services.chat_email_answer_guard_service import (
    ChatEmailAnswerGuardService,
)


class ChatEmailTurnService:
    @classmethod
    def build_prompt_supplement(
        cls,
        *,
        message: str | None,
        workspace_context: dict | None,
        email_writing_mode: bool,
        email_subtype: str | None,
    ) -> str | None:
        if not email_writing_mode:
            return None

        block = ChatEmailPromptSupplementService.build(
            message=message,
            workspace_context=workspace_context,
            email_subtype=email_subtype,
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
        return ChatEmailAnswerGuardService.apply(
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
        ChatEmailFollowUpService.attach_to_assistant_metadata(
            metadata,
            message=message,
            answer=answer,
            workspace_context=workspace_context,
        )
        ChatEmailFollowUpService.merge_guard_metadata(metadata, guard_meta)
