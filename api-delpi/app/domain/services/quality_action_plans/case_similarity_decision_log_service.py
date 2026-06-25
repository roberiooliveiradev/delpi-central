"""Log de decisão — quais casos similares influenciaram o ranking (Onda 5.5)."""

from __future__ import annotations

from typing import Any

from app.domain.services.quality_action_plans.case_similarity_scoring_service import (
    CaseSimilarityScoringService,
    IndexedCaseCandidate,
    SimilarCaseQuery,
)


class CaseSimilarityDecisionLogService:
    """Monta trilha explicável do ranking para o agente e auditoria."""

    def __init__(self, scoring: CaseSimilarityScoringService | None = None) -> None:
        self._scoring = scoring or CaseSimilarityScoringService()

    def build_from_ranked_cases(
        self,
        query: SimilarCaseQuery,
        ranked_cases: list[dict[str, Any]],
        *,
        influenced_plan_uuids: set[str] | None = None,
        min_score: float = 0.15,
    ) -> dict[str, Any]:
        influenced = influenced_plan_uuids or set()
        entries: list[dict[str, Any]] = []

        for index, case in enumerate(ranked_cases, start=1):
            plan_uuid = str(case.get("plan_uuid") or "").strip()
            entries.append(
                {
                    "rank": index,
                    "plan_id": case.get("plan_id"),
                    "plan_uuid": plan_uuid or None,
                    "similarity_score": case.get("similarity_score"),
                    "influence_factors": case.get("influence_factors") or [],
                    "influenced_suggestion": bool(plan_uuid and plan_uuid in influenced),
                }
            )

        return {
            "query_context": self._query_context(query),
            "ranking_threshold": min_score,
            "entries": entries,
            "influenced_plan_uuids": sorted(influenced),
            "top_plan_ids": [
                str(item.get("plan_id"))
                for item in ranked_cases[:5]
                if item.get("plan_id")
            ],
        }

    def enrich_ranked_cases(
        self,
        query: SimilarCaseQuery,
        candidates: list[IndexedCaseCandidate],
        *,
        limit: int = 10,
        min_score: float = 0.15,
    ) -> list[dict[str, Any]]:
        scored: list[tuple[float, list[dict[str, Any]], IndexedCaseCandidate]] = []

        for candidate in candidates:
            total, factors = self._scoring.score_breakdown(query, candidate)

            if total >= min_score:
                scored.append((total, factors, candidate))

        scored.sort(key=lambda item: item[0], reverse=True)

        return [
            {
                "plan_id": candidate.plan_code,
                "plan_uuid": candidate.plan_id,
                "similarity_score": total,
                "influence_factors": factors,
                "product_code": candidate.product_code,
                "problem_summary": candidate.problem_summary,
                "root_cause": candidate.root_cause,
                "effective_actions": candidate.effective_actions,
                "effectiveness_status": candidate.effectiveness_status,
                "closed_at": candidate.closed_at,
            }
            for total, factors, candidate in scored[:limit]
        ]

    @staticmethod
    def _query_context(query: SimilarCaseQuery) -> dict[str, Any]:
        return {
            "has_product_code": bool(query.product_code and query.product_code.strip()),
            "has_branch_code": bool(query.branch_code and query.branch_code.strip()),
            "symptom_count": len(query.symptoms),
            "has_failure_mode": bool(query.failure_mode and query.failure_mode.strip()),
            "has_root_cause_category": bool(
                query.root_cause_category and query.root_cause_category.strip()
            ),
        }
