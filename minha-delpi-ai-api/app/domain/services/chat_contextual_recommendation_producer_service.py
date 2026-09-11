"""Producer contextual de recommendations — grounding do turno; sem fallback de profile estático."""

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
    """Comparação candidate (contextual) vs static seed (observabilidade apenas)."""

    profile_key: str
    authority: str
    static_queries: tuple[str, ...]
    candidate_queries: tuple[str, ...]
    only_in_static: tuple[str, ...]
    only_in_candidate: tuple[str, ...]
    used_profile_fallback: bool
    false_suggestion_count: int
    # J-R10 — static recommendationQueries is not a selection fallback.
    static_fallback_exit_criteria: str = (
        "J-R10: recommendationQueries is observability seed only; "
        "empty candidate uses generic grounding fallback, never raw profile dump"
    )

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
            "staticFallbackRole": "REMOVED",
            "staticFallbackExitCriteria": self.static_fallback_exit_criteria,
            "legacyRecommendationFallback": 0,
        }


@dataclass(frozen=True)
class RecommendationProduceResult:
    items: tuple[dict[str, Any], ...]
    dual_run: RecommendationDualRunReport

    def as_items(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.items]


class ChatContextualRecommendationProducerService:
    """
    Autoridade no turno (J-R10):
    1) llm_candidates | existing (llm_contextual / deterministic)
    2) candidate contextual = profile queries *filtradas* (deterministic seed)
    3) generic grounding fallback (goals/facts/limitations/message) — nunca profile dump
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

        authority = "contextual_candidate"
        if not candidate_items:
            # J-R10 — generic grounding fallback (never raw recommendationQueries dump).
            authority = "contextual_generic"
            candidate_items = cls._generic_contextual_from_grounding(
                grounding,
                max_recs=max_recs,
            )

        filtered = ChatRecommendationGroundingService.filter_candidates_against_grounding(
            candidate_items,
            grounding,
        )
        items = cls._dedupe_by_query(filtered)[:max_recs]
        if not items and authority != "contextual_generic":
            authority = "contextual_generic"
            items = cls._dedupe_by_query(
                cls._generic_contextual_from_grounding(grounding, max_recs=max_recs)
            )[:max_recs]
        dual = cls._build_dual_run(
            profile_key=grounding.profile_key,
            static_queries=static_queries,
            items=items,
            authority=authority,
            used_profile_fallback=False,
        )
        return RecommendationProduceResult(items=tuple(items), dual_run=dual)

    @classmethod
    def _generic_contextual_from_grounding(
        cls,
        grounding: RecommendationGroundingContext,
        *,
        max_recs: int,
    ) -> list[dict[str, Any]]:
        caps = ChatHumanizedDataResponseContentService.recommendation_grounding_caps()
        templates = caps.get("genericFallback") if isinstance(caps, dict) else None
        if not isinstance(templates, dict):
            templates = {}

        goal_tpl = str(
            templates.get("goalLabelTemplate") or "Continuar: {goal}"
        ).strip()
        goal_reason = str(
            templates.get("goalReason") or "Próximo passo alinhado ao objetivo do turno"
        ).strip()
        lim_tpl = str(
            templates.get("limitationLabelTemplate") or "Resolver: {limitation}"
        ).strip()
        lim_reason = str(
            templates.get("limitationReason") or "Limitação observada na resposta atual"
        ).strip()
        msg_tpl = str(
            templates.get("messageLabelTemplate") or "Aprofundar: {message}"
        ).strip()
        msg_reason = str(
            templates.get("messageReason")
            or "Explorar o tema da pergunta com o catálogo autorizado"
        ).strip()

        covered = {
            token.casefold()
            for token in (
                *grounding.user_goals,
                *grounding.already_executed_goal_ids,
            )
            if token
        }
        items: list[dict[str, Any]] = []

        for goal in grounding.user_goals:
            text = str(goal or "").strip()
            if not text or text.casefold() in covered and text in grounding.already_executed_goal_ids:
                continue
            if any(
                text.casefold() == str(done or "").strip().casefold()
                for done in grounding.already_executed_goal_ids
            ):
                continue
            items.append(
                {
                    "label": goal_tpl.format(goal=text[:120]),
                    "query": text,
                    "reason": goal_reason,
                    "source": "contextual_generic",
                    "confidence": 0.5,
                }
            )
            if len(items) >= max_recs:
                return items

        for limitation in grounding.limitations:
            text = str(limitation or "").strip()
            if not text:
                continue
            items.append(
                {
                    "label": lim_tpl.format(limitation=text[:120]),
                    "query": text,
                    "reason": lim_reason,
                    "source": "contextual_generic",
                    "confidence": 0.45,
                }
            )
            if len(items) >= max_recs:
                return items

        message = str(grounding.user_message or "").strip()
        if message and len(items) < max_recs:
            items.append(
                {
                    "label": msg_tpl.format(message=message[:120]),
                    "query": message,
                    "reason": msg_reason,
                    "source": "contextual_generic",
                    "confidence": 0.4,
                }
            )

        return items

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
