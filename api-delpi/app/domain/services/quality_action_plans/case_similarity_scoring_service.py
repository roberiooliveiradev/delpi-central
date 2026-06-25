from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_TOKEN_RE = re.compile(r"[a-z0-9áàâãéêíóôõúç]+", re.IGNORECASE)


def tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    return {token.lower() for token in _TOKEN_RE.findall(text) if len(token) >= 3}


@dataclass(frozen=True)
class SimilarCaseQuery:
    problem_description: str
    product_code: str | None = None
    customer_name: str | None = None
    batch_number: str | None = None
    symptoms: tuple[str, ...] = ()
    failure_mode: str | None = None
    root_cause_category: str | None = None
    problem_category: str | None = None
    branch_code: str | None = None


@dataclass(frozen=True)
class IndexedCaseCandidate:
    plan_id: str
    plan_code: str
    search_text: str
    product_code: str | None
    failure_mode: str | None
    root_cause_category: str | None
    symptom_tags: list[str]
    problem_summary: str
    root_cause: str | None
    effectiveness_status: str | None
    closed_at: str | None
    effective_actions: list[str]
    branch_code: str | None = None
    semantic_similarity: float | None = None


class CaseSimilarityScoringService:
    """Ranking híbrido: sobreposição textual/tags + similaridade semântica (pgvector)."""

    def score(self, query: SimilarCaseQuery, candidate: IndexedCaseCandidate) -> float:
        total, _factors = self.score_breakdown(query, candidate)
        return total

    def score_breakdown(
        self,
        query: SimilarCaseQuery,
        candidate: IndexedCaseCandidate,
    ) -> tuple[float, list[dict[str, Any]]]:
        score = 0.0
        factors: list[dict[str, Any]] = []

        if candidate.semantic_similarity is not None and candidate.semantic_similarity > 0:
            weight = round(min(candidate.semantic_similarity, 1.0) * 0.4, 4)
            if weight > 0:
                score += weight
                factors.append(
                    {
                        "key": "semantic_similarity",
                        "weight": weight,
                        "score": round(candidate.semantic_similarity, 4),
                    }
                )

        query_tokens = tokenize(query.problem_description)
        candidate_tokens = tokenize(candidate.search_text)
        if query_tokens and candidate_tokens:
            overlap = len(query_tokens & candidate_tokens) / len(query_tokens | candidate_tokens)
            text_weight_cap = 0.3 if candidate.semantic_similarity else 0.45
            weight = round(overlap * text_weight_cap, 4)
            if weight > 0:
                score += weight
                factors.append(
                    {
                        "key": "text_overlap",
                        "weight": weight,
                        "shared_token_count": len(query_tokens & candidate_tokens),
                    }
                )

        query_symptoms = {s.strip().lower() for s in query.symptoms if s.strip()}
        candidate_symptoms = {s.strip().lower() for s in candidate.symptom_tags if s.strip()}
        if query_symptoms and candidate_symptoms:
            symptom_overlap = len(query_symptoms & candidate_symptoms) / len(
                query_symptoms | candidate_symptoms
            )
            weight = round(symptom_overlap * 0.25, 4)
            if weight > 0:
                score += weight
                factors.append(
                    {
                        "key": "symptom_overlap",
                        "weight": weight,
                        "matched_symptoms": sorted(query_symptoms & candidate_symptoms),
                    }
                )

        if query.product_code and candidate.product_code:
            if query.product_code.strip() == candidate.product_code.strip():
                score += 0.15
                factors.append({"key": "product_match", "weight": 0.15})

        if query.branch_code and candidate.branch_code:
            if query.branch_code.strip() == candidate.branch_code.strip():
                score += 0.12
                factors.append({"key": "branch_match", "weight": 0.12})

        if query.failure_mode and candidate.failure_mode:
            query_fm = query.failure_mode.strip().lower()
            candidate_fm = candidate.failure_mode.strip().lower()
            if query_fm in candidate_fm:
                score += 0.08
                factors.append({"key": "failure_mode_match", "weight": 0.08})
            elif candidate_fm in query_fm:
                score += 0.05
                factors.append({"key": "failure_mode_partial", "weight": 0.05})

        if query.root_cause_category and candidate.root_cause_category:
            if (
                query.root_cause_category.strip().lower()
                == candidate.root_cause_category.strip().lower()
            ):
                score += 0.07
                factors.append({"key": "root_cause_category_match", "weight": 0.07})

        if candidate.effectiveness_status == "effective":
            score += 0.05
            factors.append({"key": "effectiveness_effective", "weight": 0.05})
        elif candidate.effectiveness_status == "partially_effective":
            score += 0.02
            factors.append({"key": "effectiveness_partial", "weight": 0.02})

        return round(min(score, 1.0), 4), factors

    def rank_cases(
        self,
        query: SimilarCaseQuery,
        candidates: list[IndexedCaseCandidate],
        *,
        limit: int = 10,
        min_score: float = 0.15,
    ) -> list[dict[str, Any]]:
        ranked: list[tuple[float, IndexedCaseCandidate]] = []
        for candidate in candidates:
            similarity = self.score(query, candidate)
            if similarity >= min_score:
                ranked.append((similarity, candidate))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "plan_id": candidate.plan_code,
                "plan_uuid": candidate.plan_id,
                "similarity_score": score,
                "product_code": candidate.product_code,
                "problem_summary": candidate.problem_summary,
                "root_cause": candidate.root_cause,
                "effective_actions": candidate.effective_actions,
                "effectiveness_status": candidate.effectiveness_status,
                "closed_at": candidate.closed_at,
            }
            for score, candidate in ranked[:limit]
        ]

    def recurrence_signals(
        self,
        query: SimilarCaseQuery,
        candidates: list[IndexedCaseCandidate],
    ) -> dict[str, int]:
        same_product = 0
        same_symptom = 0
        same_root_cause = 0

        query_symptoms = {s.strip().lower() for s in query.symptoms if s.strip()}
        for candidate in candidates:
            if query.product_code and candidate.product_code == query.product_code:
                same_product += 1
            candidate_symptoms = {s.strip().lower() for s in candidate.symptom_tags if s.strip()}
            if query_symptoms and query_symptoms & candidate_symptoms:
                same_symptom += 1
            if (
                query.root_cause_category
                and candidate.root_cause_category
                and query.root_cause_category.strip().lower()
                == candidate.root_cause_category.strip().lower()
            ):
                same_root_cause += 1

        return {
            "same_product": same_product,
            "same_symptom": same_symptom,
            "same_root_cause_category": same_root_cause,
        }

    def suggested_focus_areas(self, similar_cases: list[dict[str, Any]]) -> list[str]:
        areas: list[str] = []
        for case in similar_cases[:5]:
            root_cause = (case.get("root_cause") or "").strip()
            if root_cause and root_cause not in areas:
                areas.append(root_cause[:120])
        return areas[:5]
