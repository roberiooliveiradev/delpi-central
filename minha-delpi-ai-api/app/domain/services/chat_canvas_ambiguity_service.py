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

_RICH_PRESENTATION_TYPES = frozenset({"table", "chart", "kpi", "dashboard", "tree"})


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
        last_assistant = cls._last_assistant_message(previous_messages)
        has_attachment = cls._has_recent_attachment_summary(previous_messages)

        if last_assistant is None:
            labels: list[str] = []
            if has_attachment:
                labels.append(ChatAttachmentContentService.referent_label("attachmentSummary"))
            return [label for label in labels if label]

        prose_on_last = cls._message_has_long_content(last_assistant)
        rich_on_last = cls._message_has_rich_view(last_assistant)
        rich_on_other = cls._has_rich_view_outside_message(previous_messages, last_assistant)

        # Same assistant message: prose + table/chart/kpi/dashboard = one operational result.
        if prose_on_last and rich_on_last and not has_attachment and not rich_on_other:
            return []

        labels = []

        if prose_on_last:
            labels.append(ChatAttachmentContentService.referent_label("lastResponse"))
        elif rich_on_last and not has_attachment and not rich_on_other:
            # Only rich view on last message — single referent (copy export handles it).
            return []

        if rich_on_last or rich_on_other:
            # Keep legacy label "table" for any rich operational view competing with prose/attachment.
            labels.append(ChatAttachmentContentService.referent_label("table"))

        if has_attachment:
            labels.append(ChatAttachmentContentService.referent_label("attachmentSummary"))

        # Deduplicate while preserving order.
        seen: set[str] = set()
        ordered: list[str] = []
        for label in labels:
            if not label or label in seen:
                continue
            seen.add(label)
            ordered.append(label)

        return ordered

    @classmethod
    def _last_assistant_message(cls, previous_messages: list[Any] | None) -> Any | None:
        for message in reversed(previous_messages or []):
            if cls._message_role(message) == "assistant":
                return message
        return None

    @classmethod
    def _message_role(cls, message: Any) -> str:
        return str(
            getattr(message, "role", None)
            or (message.get("role") if isinstance(message, dict) else "")
        ).strip().lower()

    @classmethod
    def _message_content(cls, message: Any) -> str:
        return str(
            getattr(message, "content", None)
            or (message.get("content") if isinstance(message, dict) else "")
        ).strip()

    @classmethod
    def _message_metadata(cls, message: Any) -> dict[str, Any]:
        metadata = (
            getattr(message, "metadata", None)
            if not isinstance(message, dict)
            else message.get("metadata")
        )
        return metadata if isinstance(metadata, dict) else {}

    @classmethod
    def _message_has_long_content(cls, message: Any) -> bool:
        min_length = ChatAttachmentContentService.min_assistant_content_length()
        return len(cls._message_content(message)) > min_length

    @classmethod
    def _message_has_rich_view(cls, message: Any) -> bool:
        metadata = cls._message_metadata(message)
        for key in (
            "presentation",
            "tablePresentation",
            "chartPresentation",
            "kpiPresentation",
            "dashboardPresentation",
            "treePresentation",
        ):
            presentation = metadata.get(key)
            if isinstance(presentation, dict):
                token = str(presentation.get("type") or "").strip().lower()
                if token in _RICH_PRESENTATION_TYPES or key != "presentation":
                    if key == "presentation" and token not in _RICH_PRESENTATION_TYPES:
                        continue
                    return True
            if isinstance(presentation, list) and presentation:
                return True

        bulk = metadata.get("tablePresentations")
        if isinstance(bulk, list) and bulk:
            return True

        for call in metadata.get("toolCalls") or metadata.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            nested = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
            presentation = call.get("presentation") or nested.get("presentation")
            if isinstance(presentation, dict) and str(presentation.get("type") or "").lower() in _RICH_PRESENTATION_TYPES:
                return True
            for key in ("tablePresentation", "chartPresentation", "kpiPresentation"):
                slot = nested.get(key)
                if isinstance(slot, dict):
                    return True
                if isinstance(slot, list) and slot:
                    return True

        return False

    @classmethod
    def _has_rich_view_outside_message(
        cls,
        previous_messages: list[Any] | None,
        excluded: Any,
    ) -> bool:
        excluded_id = None
        if isinstance(excluded, dict):
            excluded_id = excluded.get("id")
        else:
            excluded_id = getattr(excluded, "id", None)

        for message in previous_messages or []:
            if message is excluded:
                continue
            if excluded_id is not None:
                msg_id = (
                    message.get("id")
                    if isinstance(message, dict)
                    else getattr(message, "id", None)
                )
                if msg_id == excluded_id:
                    continue
            if cls._message_role(message) != "assistant":
                continue
            if cls._message_has_rich_view(message):
                return True

        return False

    @classmethod
    def _has_recent_assistant_content(cls, previous_messages: list[Any] | None) -> bool:
        for message in reversed(previous_messages or []):
            if cls._message_role(message) != "assistant":
                continue
            if cls._message_has_long_content(message):
                return True
        return False

    @classmethod
    def _has_recent_table(cls, previous_messages: list[Any] | None) -> bool:
        for message in reversed(previous_messages or []):
            if cls._message_has_rich_view(message):
                return True
        return False

    @classmethod
    def _has_recent_attachment_summary(cls, previous_messages: list[Any] | None) -> bool:
        for message in reversed(previous_messages or []):
            metadata = cls._message_metadata(message)

            summaries = metadata.get("attachmentSummaries") or []

            if isinstance(summaries, list) and summaries:
                return True

            attachments = metadata.get("attachments") or []

            if isinstance(attachments, list) and attachments:
                return True

        return False
