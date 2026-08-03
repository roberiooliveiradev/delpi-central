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
        normalized = str(query or "").lower()
        rules = ExternalActionResponseContentService.object_list(
            "actionSelection",
            "candidateDiscovery",
            "rules",
        )

        for rule in rules:
            terms = rule.get("anyOfTerms") or []
            if not isinstance(terms, list):
                continue
            if any(str(term).lower() in normalized for term in terms if str(term).strip()):
                return rule

        return None

    @classmethod
    def resolve_path_markers(cls, message: str) -> list[str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        pools = ExternalActionResponseContentService.object_list(
            "actionSelection",
            "candidateDiscovery",
            "markerPools",
        )
        markers: list[str] = []
        seen: set[str] = set()

        for pool in pools:
            term_keys = pool.get("anyOfTermKeys") or []
            if isinstance(term_keys, list) and term_keys:
                if not cls._message_has_any_key(normalized, term_keys):
                    continue

            for marker in cls._markers_from_pool(pool):
                key = marker.lower()
                if key in seen:
                    continue
                seen.add(key)
                markers.append(marker)

        return markers

    @classmethod
    def _message_has_any_key(cls, normalized: str, term_keys: list[Any]) -> bool:
        for key in term_keys:
            parts = tuple(part for part in str(key).split(".") if part)
            terms = ExternalActionResponseContentService.list("actionSelection", *parts)
            if any(term in normalized for term in terms):
                return True
        return False

    @classmethod
    def _markers_from_pool(cls, pool: dict) -> list[str]:
        direct = pool.get("pathMarkers")
        if isinstance(direct, list):
            return [str(item) for item in direct if str(item).strip()]

        key = str(pool.get("pathMarkersKey") or "").strip()
        if not key:
            return []
        parts = tuple(part for part in key.split(".") if part)
        return ExternalActionResponseContentService.list("actionSelection", *parts)
