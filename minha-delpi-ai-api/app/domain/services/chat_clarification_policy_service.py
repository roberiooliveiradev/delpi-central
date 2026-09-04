"""Política canônica de clarificação — material vs discoverable (E1.S3).

Heurísticas emitem candidatos; este serviço decide clarify vs continue.
Distinto de ``ChatClarifyPolicyService`` (grounding slot/ungrounded).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "clarification_policy"


@dataclass(frozen=True)
class ClarificationCandidate:
    code: str
    material: bool = True
    discoverable: bool = False
    answer: str | None = None


@dataclass(frozen=True)
class ClarificationDecision:
    action: Literal["clarify", "continue"]
    reason_code: str
    answer: str | None = None
    candidate_code: str | None = None

    def to_admin_debug(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "reasonCode": self.reason_code,
            "candidateCode": self.candidate_code,
            "hasAnswer": bool(self.answer),
        }


class ChatClarificationPolicyService:
    @classmethod
    def _reason(cls, key: str, default: str) -> str:
        node = ChatAssistantContentService.get_node(_BUNDLE, "reasonCodes") or {}
        if isinstance(node, dict) and node.get(key):
            return str(node[key])
        return default

    @classmethod
    def _codes(cls, section: str) -> frozenset[str]:
        raw = ChatAssistantContentService.get_node(_BUNDLE, section) or []
        if not isinstance(raw, list):
            return frozenset()
        return frozenset(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def decide(
        cls,
        candidates: list[ClarificationCandidate] | None,
        *,
        message: str = "",
    ) -> ClarificationDecision:
        from app.domain.services.chat_product_search_intent_service import (
            ChatProductSearchIntentService,
        )

        if ChatProductSearchIntentService.looks_like_product_search(message):
            return ClarificationDecision(
                action="continue",
                reason_code=cls._reason(
                    "skipped_discoverable_search",
                    "skipped_discoverable_search",
                ),
                candidate_code="product_search",
            )

        items = list(candidates or [])
        if not items:
            return ClarificationDecision(
                action="continue",
                reason_code=cls._reason(
                    "continue_no_ambiguity",
                    "continue_no_ambiguity",
                ),
            )

        discoverable = cls._codes("discoverableCodes")
        material = cls._codes("materialMissingCodes")

        for item in items:
            code = str(item.code or "").strip()
            if item.discoverable or code in discoverable:
                return ClarificationDecision(
                    action="continue",
                    reason_code=cls._reason(
                        "skipped_discoverable",
                        "skipped_discoverable",
                    ),
                    candidate_code=code or None,
                )

        for item in items:
            code = str(item.code or "").strip()
            if item.material or code in material:
                return ClarificationDecision(
                    action="clarify",
                    reason_code=cls._reason(
                        "clarify_material_missing",
                        "clarify_material_missing",
                    ),
                    answer=item.answer,
                    candidate_code=code or None,
                )

        return ClarificationDecision(
            action="continue",
            reason_code=cls._reason(
                "continue_no_ambiguity",
                "continue_no_ambiguity",
            ),
        )

    @classmethod
    def evaluate_turn_analysis_clarify(
        cls,
        message: str,
        *,
        clarify_answer: str | None = None,
    ) -> ClarificationDecision:
        """Gate pós-TurnAnalysis: clarify genérico não mata tools discoverable."""
        decision = cls.decide([], message=message)
        if decision.action == "continue":
            return decision

        return ClarificationDecision(
            action="clarify",
            reason_code=cls._reason(
                "clarify_turn_analysis",
                "clarify_turn_analysis",
            ),
            answer=clarify_answer,
            candidate_code="turn_analysis",
        )

    @classmethod
    def evaluate_missing_product_code(
        cls,
        message: str,
        *,
        answer: str | None,
    ) -> ClarificationDecision:
        if not answer:
            return ClarificationDecision(
                action="continue",
                reason_code=cls._reason(
                    "continue_no_ambiguity",
                    "continue_no_ambiguity",
                ),
            )

        return cls.decide(
            [
                ClarificationCandidate(
                    code="missing_product_code",
                    material=True,
                    discoverable=False,
                    answer=answer,
                )
            ],
            message=message,
        )
