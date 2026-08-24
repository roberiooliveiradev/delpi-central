"""Avalia se o turno tem referente conversacional (artefato, foco ou slot)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)


class ChatTurnGroundingStatus(str, Enum):
    GROUNDED = "grounded"
    SCHEMA_SLOT_MISSING = "schema_slot_missing"
    AMBIGUOUS_MULTI_ARTIFACT = "ambiguous_multi_artifact"
    UNGROUNDED = "ungrounded"


@dataclass(frozen=True)
class ChatTurnGrounding:
    status: ChatTurnGroundingStatus
    reason: str
    excerpt: dict[str, Any] | None = None
    referring_label: str | None = None

    @property
    def is_grounded(self) -> bool:
        return self.status == ChatTurnGroundingStatus.GROUNDED

    def to_metadata(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status.value,
            "reason": self.reason,
        }

        if self.referring_label:
            payload["referringTo"] = {"label": self.referring_label}

        if isinstance(self.excerpt, dict) and self.excerpt:
            payload["excerpt"] = {
                key: self.excerpt.get(key)
                for key in (
                    "operationId",
                    "profileKey",
                    "entity",
                    "presentationType",
                    "title",
                    "rowCount",
                    "topKeys",
                    "messageId",
                )
                if self.excerpt.get(key) is not None
            }

        return payload


class ChatTurnGroundingService:
    @classmethod
    def evaluate(
        cls,
        *,
        message: str,
        snapshot: dict[str, Any] | None,
        previous_messages: list[Any] | None = None,
    ) -> ChatTurnGrounding:
        snapshot = dict(snapshot or {})
        excerpt = snapshot.get("lastResultExcerpt")

        if isinstance(excerpt, dict) and excerpt:
            return cls._grounded(
                reason="last_result_excerpt",
                excerpt=excerpt,
            )

        last_presentation = snapshot.get("lastPresentation")

        if isinstance(last_presentation, dict) and last_presentation.get("type"):
            return cls._grounded(
                reason="last_presentation",
                excerpt=excerpt if isinstance(excerpt, dict) else None,
                title=str(last_presentation.get("title") or "").strip() or None,
                row_count=None,
            )

        operational_focus = snapshot.get("operationalFocus") or {}

        if (
            isinstance(operational_focus, dict)
            and operational_focus.get("productCode")
            and ChatFollowUpIntentService.is_operational_follow_up(message)
        ):
            return cls._grounded(
                reason="operational_focus_follow_up",
                excerpt=excerpt if isinstance(excerpt, dict) else None,
            )

        if cls._has_recent_tool_success(previous_messages):
            return cls._grounded(
                reason="recent_tool_success",
                excerpt=excerpt if isinstance(excerpt, dict) else None,
            )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        if not normalized:
            return ChatTurnGrounding(
                status=ChatTurnGroundingStatus.UNGROUNDED,
                reason="empty_message",
            )

        return ChatTurnGrounding(
            status=ChatTurnGroundingStatus.UNGROUNDED,
            reason="no_referent",
        )

    @classmethod
    def _grounded(
        cls,
        *,
        reason: str,
        excerpt: dict[str, Any] | None,
        title: str | None = None,
        row_count: int | None = None,
    ) -> ChatTurnGrounding:
        label = None

        if isinstance(excerpt, dict):
            label = ChatTurnGroundingContentService.referring_to_label(
                title=str(excerpt.get("title") or title or "").strip() or None,
                row_count=excerpt.get("rowCount")
                if excerpt.get("rowCount") is not None
                else row_count,
            )
        elif title:
            label = ChatTurnGroundingContentService.referring_to_label(
                title=title,
                row_count=row_count,
            )

        return ChatTurnGrounding(
            status=ChatTurnGroundingStatus.GROUNDED,
            reason=reason,
            excerpt=excerpt if isinstance(excerpt, dict) else None,
            referring_label=label,
        )

    @classmethod
    def _has_recent_tool_success(cls, previous_messages: list[Any] | None) -> bool:
        for item in reversed(previous_messages or []):
            role = str(
                getattr(item, "role", None) or (item.get("role") if isinstance(item, dict) else "")
            ).strip()

            if role != "assistant":
                continue

            metadata = getattr(item, "metadata", None)

            if metadata is None and isinstance(item, dict):
                metadata = item.get("metadata")

            if not isinstance(metadata, dict):
                continue

            for tool_call in metadata.get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if isinstance(tool_meta, dict) and tool_meta.get("ok"):
                    return True

            return False

        return False
