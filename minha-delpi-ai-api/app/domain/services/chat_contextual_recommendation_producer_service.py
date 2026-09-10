"""Producer contextual de recommendations (E6.S3) — delta LLM=0; prefer llm_candidates se presentes."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)
from app.domain.services.chat_recommendation_grounding_service import (
    ChatRecommendationGroundingService,
    RecommendationGroundingContext,
)

_PAGINATION_MARKERS = (
    "próxima página",
    "proxima pagina",
    "página seguinte",
    "pagina seguinte",
    "next page",
)


class ChatContextualRecommendationProducerService:
    """
    Ordem de autoridade no turno:
    1) candidatos já presentes / llm_candidates (source llm_contextual)
    2) profile queries filtradas por grounding (source deterministic | profile_fallback)
    """

    @classmethod
    def produce(
        cls,
        *,
        grounding: RecommendationGroundingContext,
        profile_queries: list[dict[str, str]] | None = None,
        llm_candidates: list[Any] | None = None,
        existing_candidates: list[Any] | None = None,
    ) -> list[dict[str, Any]]:
        caps = ChatHumanizedDataResponseContentService.recommendation_grounding_caps()
        max_recs = max(0, int(caps.get("maxRecommendations") or 3))

        primary = list(llm_candidates or []) or list(existing_candidates or [])
        if primary:
            normalized: list[dict[str, Any]] = []
            for item in primary:
                if not isinstance(item, dict):
                    continue
                payload = dict(item)
                if not str(payload.get("source") or "").strip():
                    payload["source"] = (
                        "llm_contextual" if llm_candidates else "deterministic"
                    )
                normalized.append(payload)
            filtered = ChatRecommendationGroundingService.filter_candidates_against_grounding(
                normalized,
                grounding,
            )
            return cls._dedupe_by_query(filtered)[:max_recs]

        queries = profile_queries
        if queries is None:
            queries = ChatHumanizedDataResponseContentService.recommendation_queries(
                grounding.profile_key
            )

        candidates: list[dict[str, Any]] = []
        for item in queries or []:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()
            if not label or not query:
                continue
            if cls._should_skip_profile_query(query, grounding):
                continue
            candidates.append(
                {
                    "label": label,
                    "query": query,
                    "reason": str(item.get("reason") or "").strip(),
                    "source": "deterministic",
                    "confidence": 0.55,
                }
            )

        if not candidates and queries:
            # Nenhum filtro contextual aplicável — fallback explícito do profile.
            for item in queries:
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label") or "").strip()
                query = str(item.get("query") or "").strip()
                if not label or not query:
                    continue
                candidates.append(
                    {
                        "label": label,
                        "query": query,
                        "reason": str(item.get("reason") or "").strip(),
                        "source": "profile_fallback",
                        "confidence": 0.4,
                    }
                )

        filtered = ChatRecommendationGroundingService.filter_candidates_against_grounding(
            candidates,
            grounding,
        )
        return cls._dedupe_by_query(filtered)[:max_recs]

    @classmethod
    def _should_skip_profile_query(
        cls,
        query: str,
        grounding: RecommendationGroundingContext,
    ) -> bool:
        q = query.casefold()
        if any(marker in q for marker in _PAGINATION_MARKERS):
            if not cls._has_pagination_signal(grounding):
                return True
        # Anti-redundância leve: query idêntica a goal/fact já coberto não sobe.
        covered = {
            token.casefold()
            for token in (
                *grounding.user_goals,
                *grounding.already_executed_goal_ids,
            )
            if token
        }
        if q in covered:
            return True
        return False

    @classmethod
    def _has_pagination_signal(cls, grounding: RecommendationGroundingContext) -> bool:
        blob = " ".join(grounding.limitations).casefold()
        if any(
            token in blob
            for token in ("página", "pagina", "paginaç", "truncad", "hasmore", "parcial")
        ):
            return True
        return False

    @classmethod
    def _dedupe_by_query(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        output: list[dict[str, Any]] = []
        for item in items:
            key = str(item.get("query") or "").strip().casefold()
            if not key or key in seen:
                continue
            seen.add(key)
            output.append(item)
        return output
