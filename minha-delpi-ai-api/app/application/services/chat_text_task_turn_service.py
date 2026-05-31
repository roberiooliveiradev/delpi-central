"""Turno unificado para tarefas textuais — Playbook 03."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_text_task_service import ChatTextTaskService


class ChatTextTaskTurnService:
    @classmethod
    def build_prompt_supplement(
        cls,
        *,
        message: str | None,
        text_task_mode: bool,
        text_correction_mode: bool = False,
        text_correction_subtype: str | None = None,
        email_writing_mode: bool = False,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
    ) -> str | None:
        if not text_task_mode:
            return None

        return ChatTextTaskService.build_prompt_supplement(
            message=message,
            workspace_context=workspace_context,
            previous_messages=previous_messages,
            text_correction_mode=text_correction_mode,
            text_correction_subtype=text_correction_subtype,
            email_writing_mode=email_writing_mode,
        )

    @classmethod
    def attach_follow_up_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None,
        answer: str | None,
        workspace_context: dict | None,
        text_task_mode: bool,
        correction_guard_meta: dict[str, Any] | None = None,
        canvas_updated: bool = False,
        pipeline_stages: list[str] | None = None,
        tool_context: dict | None = None,
        canvas_title: str | None = None,
        canvas_markdown: str | None = None,
        previous_messages: list | None = None,
    ) -> None:
        if not text_task_mode:
            return

        from app.application.services.chat_text_correction_turn_service import (
            ChatTextCorrectionTurnService,
        )

        ChatTextCorrectionTurnService.attach_follow_up_metadata(
            metadata,
            message=message,
            answer=answer,
            workspace_context=workspace_context,
            guard_meta=correction_guard_meta,
            canvas_updated=canvas_updated,
        )

        from app.application.services.chat_text_task_follow_up_service import (
            ChatTextTaskFollowUpService,
        )

        ChatTextTaskFollowUpService.attach_to_assistant_metadata(
            metadata,
            message=message,
            answer=answer,
            workspace_context=workspace_context,
        )

        from app.application.services.chat_text_task_mixed_turn_service import (
            ChatTextTaskMixedTurnService,
        )

        ChatTextTaskMixedTurnService.attach_to_assistant_metadata(
            metadata,
            message=message,
            pipeline_stages=pipeline_stages,
            tool_context=tool_context,
        )

        if canvas_updated and canvas_markdown:
            from app.application.services.chat_text_task_canvas_service import (
                ChatTextTaskCanvasService,
            )

            ChatTextTaskCanvasService.attach_version_history(
                metadata,
                previous_messages=previous_messages,
                new_markdown=canvas_markdown,
                title=canvas_title or "Texto na lousa",
            )
