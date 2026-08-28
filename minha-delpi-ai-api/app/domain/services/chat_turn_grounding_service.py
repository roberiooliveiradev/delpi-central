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
                    "keysByComponentType",
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
    def should_narrate_excerpt(
        cls,
        message: str,
        excerpt: dict[str, Any] | None,
    ) -> bool:
        if not isinstance(excerpt, dict) or not excerpt:
            return False

        if cls.should_enrich_before_insight(message, excerpt):
            return False

        if cls.should_narrate_insight_only(message):
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        if not normalized:
            return False

        if cls._should_expand_from_excerpt(normalized):
            return False

        has_content = bool(excerpt.get("preview")) or bool(excerpt.get("topKeys"))
        row_count = excerpt.get("rowCount")

        if not has_content and not (isinstance(row_count, int) and row_count > 0):
            return False

        return True

    @classmethod
    def should_enrich_before_insight(
        cls,
        message: str,
        excerpt: dict[str, Any] | None,
    ) -> bool:
        if not isinstance(excerpt, dict) or not excerpt:
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        if not normalized:
            return False

        if not cls._normalized_contains_any(
            normalized,
            ChatTurnGroundingContentService.insight_enrich_triggers(),
        ):
            return False

        keys_by_type = excerpt.get("keysByComponentType")

        if isinstance(keys_by_type, dict) and any(
            isinstance(values, list) and values for values in keys_by_type.values()
        ):
            return True

        return cls._message_requests_fan_out(message)

    @classmethod
    def should_narrate_insight_only(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        if not normalized:
            return False

        return cls._normalized_contains_any(
            normalized,
            ChatTurnGroundingContentService.insight_narrate_triggers(),
        )

    @classmethod
    def resolve_grounded_stage(
        cls,
        *,
        message: str,
        excerpt: dict[str, Any] | None,
        last_action: dict[str, Any] | None = None,
        operational_focus: dict[str, Any] | None = None,
    ) -> str | None:
        from app.domain.services.chat_follow_up_turn_interpretation_service import (
            ChatFollowUpTurnInterpretationService,
        )

        interpretation = ChatFollowUpTurnInterpretationService.interpret(
            message=message,
            last_action=last_action,
            last_result_excerpt=excerpt,
            operational_focus=operational_focus,
        )
        follow_up_stage = ChatFollowUpTurnInterpretationService.grounded_stage_for(
            interpretation
        )

        if follow_up_stage in {
            "grounded_revise_query",
            "grounded_challenge_result",
            "grounded_clarify_slot",
        }:
            return follow_up_stage

        if interpretation.decision == "narrate_recap" and follow_up_stage:
            return follow_up_stage

        if interpretation.suppress_broad_narrate and interpretation.decision == "new_intent":
            if interpretation.reason == "defer_enrich_insight":
                if cls.should_enrich_before_insight(message, excerpt):
                    return "grounded_enrich_insight"
            return None

        if cls.should_enrich_before_insight(message, excerpt):
            return "grounded_enrich_insight"

        if cls.should_narrate_insight_only(message):
            return "grounded_narrate_insight"

        if interpretation.suppress_broad_narrate:
            return None

        if cls.should_narrate_excerpt(message, excerpt):
            return "grounded_narrate_recap"

        return None

    @classmethod
    def _message_requests_fan_out(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        if not normalized:
            return False

        for token in ChatTurnGroundingContentService.fan_out_on_referent_items():
            candidate = ChatMessageNormalizationService.normalize_for_matching(token)

            if candidate and candidate in normalized:
                return True

        return False

    @classmethod
    def should_expand_from_excerpt(
        cls,
        message: str,
        excerpt: dict[str, Any] | None,
    ) -> bool:
        if not isinstance(excerpt, dict) or not excerpt:
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        if not normalized:
            return False

        return cls._should_expand_from_excerpt(normalized)

    @classmethod
    def resolve_referent_component_type(cls, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        if not normalized:
            return None

        triggers = ChatTurnGroundingContentService.referent_type_triggers()
        best_type: str | None = None
        best_length = 0

        for component_type, tokens in triggers.items():
            for token in tokens:
                candidate = ChatMessageNormalizationService.normalize_for_matching(token)

                if not candidate or candidate not in normalized:
                    continue

                if len(candidate) > best_length:
                    best_type = component_type
                    best_length = len(candidate)

        return best_type

    @classmethod
    def _should_expand_from_excerpt(cls, normalized: str) -> bool:
        expand_triggers = ChatTurnGroundingContentService.expand_triggers()
        fan_out_triggers = ChatTurnGroundingContentService.fan_out_on_referent_items()

        if cls._normalized_contains_any(normalized, expand_triggers):
            return True

        if cls._normalized_contains_any(normalized, fan_out_triggers):
            return cls._normalized_contains_any(normalized, expand_triggers)

        return False

    @staticmethod
    def _normalized_contains_any(normalized: str, triggers: tuple[str, ...]) -> bool:
        for token in triggers:
            candidate = ChatMessageNormalizationService.normalize_for_matching(token)

            if candidate and candidate in normalized:
                return True

        return False

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
