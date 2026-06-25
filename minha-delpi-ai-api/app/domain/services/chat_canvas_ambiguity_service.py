"""Ambiguidade em «coloque isso na lousa» — Playbook 05 §23."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_attachment_content_service import (
    ChatAttachmentContentService,
)
from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatCanvasAmbiguityService:
    @classmethod
    def is_deictic_canvas_request(cls, message: str) -> bool:
        if not ChatCanvasIntentService.is_canvas_placement_request(message):
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        return any(term in normalized for term in ChatAttachmentContentService.deictic_terms())

    @classmethod
    def build_clarification_answer(cls, *, previous_messages: list[Any] | None) -> str | None:
        candidates = cls._list_referent_labels(previous_messages)

        if len(candidates) < 2:
            return None

        return ChatAttachmentContentService.clarification_answer(candidates)

    @classmethod
    def _list_referent_labels(cls, previous_messages: list[Any] | None) -> list[str]:
        labels: list[str] = []

        if cls._has_recent_assistant_content(previous_messages):
            labels.append(
                ChatAttachmentContentService.referent_label("lastResponse")
            )

        if cls._has_recent_table(previous_messages):
            labels.append(ChatAttachmentContentService.referent_label("table"))

        if cls._has_recent_attachment_summary(previous_messages):
            labels.append(
                ChatAttachmentContentService.referent_label("attachmentSummary")
            )

        return [label for label in labels if label]

    @classmethod
    def _has_recent_assistant_content(cls, previous_messages: list[Any] | None) -> bool:
        min_length = ChatAttachmentContentService.min_assistant_content_length()

        for message in reversed(previous_messages or []):
            role = str(getattr(message, "role", None) or (message.get("role") if isinstance(message, dict) else ""))

            if role != "assistant":
                continue

            content = str(
                getattr(message, "content", None)
                or (message.get("content") if isinstance(message, dict) else "")
            ).strip()

            if len(content) > min_length:
                return True

        return False

    @classmethod
    def _has_recent_table(cls, previous_messages: list[Any] | None) -> bool:
        for message in reversed(previous_messages or []):
            metadata = (
                getattr(message, "metadata", None)
                if not isinstance(message, dict)
                else message.get("metadata")
            )

            if not isinstance(metadata, dict):
                continue

            tool_calls = metadata.get("toolCalls") or metadata.get("tool_calls") or []

            for call in tool_calls:
                if not isinstance(call, dict):
                    continue

                presentation = call.get("presentation") or call.get("metadata", {}).get("presentation")

                if isinstance(presentation, dict) and presentation.get("type") == "table":
                    return True

        return False

    @classmethod
    def _has_recent_attachment_summary(cls, previous_messages: list[Any] | None) -> bool:
        for message in reversed(previous_messages or []):
            metadata = (
                getattr(message, "metadata", None)
                if not isinstance(message, dict)
                else message.get("metadata")
            )

            if not isinstance(metadata, dict):
                continue

            summaries = metadata.get("attachmentSummaries") or []

            if isinstance(summaries, list) and summaries:
                return True

            attachments = metadata.get("attachments") or []

            if isinstance(attachments, list) and attachments:
                return True

        return False
