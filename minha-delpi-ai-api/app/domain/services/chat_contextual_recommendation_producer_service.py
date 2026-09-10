"""Producer contextual de recommendations — candidate-first; recommendationQueries = LEGACY_FALLBACK."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class RecommendationDualRunReport:
    """Comparação candidate (contextual) vs static (recommendationQueries bruto)."""

    profile_key: str
    authority: str
    static_queries: tuple[str, ...]
    candidate_queries: tuple[str, ...]
    only_in_static: tuple[str, ...]
    only_in_candidate: tuple[str, ...]
    used_profile_fallback: bool
    false_suggestion_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "profileKey": self.profile_key,
            "authority": self.authority,
            "staticQueryCount": len(self.static_queries),
            "candidateQueryCount": len(self.candidate_queries),
            "staticQueries": list(self.static_queries),
            "candidateQueries": list(self.candidate_queries),
            "onlyInStatic": list(self.only_in_static),
            "onlyInCandidate": list(self.only_in_candidate),
            "usedProfileFallback": self.used_profile_fallback,
            "falseSuggestionCount": self.false_suggestion_count,
        }


@dataclass(frozen=True)
class RecommendationProduceResult:
    items: tuple[dict[str, Any], ...]
    dual_run: RecommendationDualRunReport

    def as_items(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.items]


class ChatContextualRecommendationProducerService:
    """
    Autoridade no turno (E6.S4):
    1) llm_candidates | existing (llm_contextual / deterministic)
    2) candidate contextual = profile queries *filtradas* (deterministic)
    3) LEGACY_FALLBACK = recommendationQueries bruto só se candidate vazio
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
        return cls.produce_with_dual_run(
            grounding=grounding,
            profile_queries=profile_queries,
            llm_candidates=llm_candidates,
            existing_candidates=existing_candidates,
        ).as_items()

    @classmethod
    def produce_with_dual_run(
        cls,
        *,
        grounding: RecommendationGroundingContext,
        profile_queries: list[dict[str, str]] | None = None,
        llm_candidates: list[Any] | None = None,
        existing_candidates: list[Any] | None = None,
    ) -> RecommendationProduceResult:
        caps = ChatHumanizedDataResponseContentService.recommendation_grounding_caps()
        max_recs = max(0, int(caps.get("maxRecommendations") or 3))

        queries = profile_queries
        if queries is None:
            queries = ChatHumanizedDataResponseContentService.recommendation_queries(
                grounding.profile_key
            )
        static_queries = tuple(
            str(item.get("query") or "").strip()
            for item in (queries or [])
            if isinstance(item, dict) and str(item.get("query") or "").strip()
        )

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
            items = cls._dedupe_by_query(filtered)[:max_recs]
            dual = cls._build_dual_run(
                profile_key=grounding.profile_key,
                static_queries=static_queries,
                items=items,
                authority="llm_or_existing",
                used_profile_fallback=False,
            )
            return RecommendationProduceResult(items=tuple(items), dual_run=dual)

        candidate_items: list[dict[str, Any]] = []
        for item in queries or []:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()
            if not label or not query:
                continue
            if cls._should_skip_profile_query(query, grounding):
                continue
            candidate_items.append(
                {
                    "label": label,
                    "query": query,
                    "reason": str(item.get("reason") or "").strip(),
                    "source": "deterministic",
                    "confidence": 0.55,
                }
            )

        used_fallback = False
        authority = "contextual_candidate"
        if not candidate_items and queries:
            # LEGACY_FALLBACK: recommendationQueries bruto só quando candidate vazio.
            used_fallback = True
            authority = "profile_fallback"
            for item in queries:
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label") or "").strip()
                query = str(item.get("query") or "").strip()
                if not label or not query:
                    continue
                candidate_items.append(
                    {
                        "label": label,
                        "query": query,
                        "reason": str(item.get("reason") or "").strip(),
                        "source": "profile_fallback",
                        "confidence": 0.4,
                    }
                )

        filtered = ChatRecommendationGroundingService.filter_candidates_against_grounding(
            candidate_items,
            grounding,
        )
        items = cls._dedupe_by_query(filtered)[:max_recs]
        dual = cls._build_dual_run(
            profile_key=grounding.profile_key,
            static_queries=static_queries,
            items=items,
            authority=authority,
            used_profile_fallback=used_fallback,
        )
        return RecommendationProduceResult(items=tuple(items), dual_run=dual)

    @classmethod
    def _build_dual_run(
        cls,
        *,
        profile_key: str,
        static_queries: tuple[str, ...],
        items: list[dict[str, Any]],
        authority: str,
        used_profile_fallback: bool,
    ) -> RecommendationDualRunReport:
        candidate = tuple(
            str(item.get("query") or "").strip()
            for item in items
            if str(item.get("query") or "").strip()
        )
        static_fold = {q.casefold(): q for q in static_queries}
        candidate_fold = {q.casefold(): q for q in candidate}
        only_static = tuple(
            static_fold[k] for k in static_fold.keys() - candidate_fold.keys()
        )
        only_candidate = tuple(
            candidate_fold[k] for k in candidate_fold.keys() - static_fold.keys()
        )
        # False suggestion: query no candidate que não existia no catálogo estático do profile.
        # (llm_candidates podem legítimamente divergir; ainda assim contabilizamos.)
        return RecommendationDualRunReport(
            profile_key=str(profile_key or "").strip(),
            authority=authority,
            static_queries=static_queries,
            candidate_queries=candidate,
            only_in_static=only_static,
            only_in_candidate=only_candidate,
            used_profile_fallback=used_profile_fallback,
            false_suggestion_count=len(only_candidate),
        )

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
        return any(
            token in blob
            for token in ("página", "pagina", "paginaç", "truncad", "hasmore", "parcial")
        )

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
