"""Descoberta de candidatos OpenAPI — keywords e pools de path em JSON."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionCandidateDiscoveryService:
    # After normalize, short tokens like "ov" (from " ov ") must not match inside
    # words such as "provider" — that emptied logistics allowlists (E9.S14).
    _SHORT_TERM_MAX_LEN = 3

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
            if any(cls._term_matches(str(term), normalized) for term in terms):
                return rule

        return None

    @classmethod
    def _term_matches(cls, term: str, normalized_message: str) -> bool:
        raw = str(term or "")
        if not raw.strip():
            return False

        token = ChatMessageNormalizationService.normalize_for_matching(raw)
        if not token:
            return False

        # Spaced catalog markers (e.g. " ov ") or very short tokens → word boundary.
        needs_boundary = len(token) <= cls._SHORT_TERM_MAX_LEN or bool(
            re.search(r"\s", raw)
        )
        if needs_boundary:
            return (
                re.search(rf"(?<!\w){re.escape(token)}(?!\w)", normalized_message)
                is not None
            )

        return token in normalized_message
