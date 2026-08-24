"""Política canônica de clarificação — slot, referente ou ausência real."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)
from app.domain.services.chat_turn_grounding_service import ChatTurnGrounding


class ChatClarifyPolicyKind(str, Enum):
    NONE = "none"
    SLOT = "slot"
    UNGROUNDED = "ungrounded"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class ChatClarifyPolicy:
    kind: ChatClarifyPolicyKind
    answer_key: str | None = None
    answer: str | None = None


class ChatClarifyPolicyService:
    @classmethod
    def resolve(
        cls,
        grounding: ChatTurnGrounding,
        *,
        missing_slot_answer: str | None = None,
        ambiguous: bool = False,
    ) -> ChatClarifyPolicy:
        if grounding.is_grounded:
            if ambiguous:
                answer = ChatTurnGroundingContentService.clarify_ambiguous_artifact()

                return ChatClarifyPolicy(
                    kind=ChatClarifyPolicyKind.AMBIGUOUS,
                    answer_key="ambiguousWhichArtifact",
                    answer=answer or None,
                )

            return ChatClarifyPolicy(kind=ChatClarifyPolicyKind.NONE)

        if str(missing_slot_answer or "").strip():
            return ChatClarifyPolicy(
                kind=ChatClarifyPolicyKind.SLOT,
                answer=str(missing_slot_answer).strip(),
            )

        return ChatClarifyPolicy(kind=ChatClarifyPolicyKind.UNGROUNDED)
