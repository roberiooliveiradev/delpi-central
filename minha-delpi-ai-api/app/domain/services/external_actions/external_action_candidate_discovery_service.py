"""Descoberta de candidatos OpenAPI — keywords e pools de path em JSON."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionCandidateDiscoveryService:
    @classmethod
    def match_filter_rule(cls, query: str) -> dict | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(query)
        rules = ExternalActionResponseContentService.object_list(
            "actionSelection",
            "candidateDiscovery",
            "rules",
        )

        for rule in rules:
            terms = rule.get("anyOfTerms") or []
            if not isinstance(terms, list):
                continue
            if any(
                ChatMessageNormalizationService.normalize_for_matching(str(term))
                in normalized
                for term in terms
                if str(term).strip()
            ):
                return rule

        return None
