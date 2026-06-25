from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.services.quality_action_plans.case_similarity_decision_log_service import (
    CaseSimilarityDecisionLogService,
)
from app.domain.services.quality_action_plans.case_similarity_scoring_service import (
    CaseSimilarityScoringService,
    IndexedCaseCandidate,
    SimilarCaseQuery,
)


class CaseSimilarityIndexRepository(Protocol):
    def sync_case_similarity_index(self, plan_id: str) -> None: ...


class SimilarCasesSearchRepository(Protocol):
    def fetch_similar_case_candidates(
        self,
        *,
        problem_description: str,
        product_code: str | None,
        symptoms: list[str],
        branch_code: str | None = None,
        exclude_plan_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...


class PlanDetailReader(Protocol):
    def get_plan_detail(self, plan_id: str) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class SimilarCasesRequest:
    problem_description: str
    product_code: str | None = None
    customer_name: str | None = None
    batch_number: str | None = None
    symptoms: list[str] | None = None
    failure_mode: str | None = None
    root_cause_category: str | None = None
    problem_category: str | None = None
    branch_code: str | None = None
    exclude_plan_id: str | None = None


class SyncCaseSimilarityIndexUseCase:
    def __init__(self, repository: CaseSimilarityIndexRepository) -> None:
        self._repository = repository

    def execute(self, plan_id: str) -> None:
        self._repository.sync_case_similarity_index(plan_id)


class SearchSimilarCasesUseCase:
    def __init__(
        self,
        repository: SimilarCasesSearchRepository,
        scoring: CaseSimilarityScoringService | None = None,
        decision_log: CaseSimilarityDecisionLogService | None = None,
    ) -> None:
        self._repository = repository
        self._scoring = scoring or CaseSimilarityScoringService()
        self._decision_log = decision_log or CaseSimilarityDecisionLogService(self._scoring)

    def execute(self, request: SimilarCasesRequest) -> dict[str, Any]:
        if not request.problem_description.strip():
            raise ValueError("problem_description é obrigatório.")

        query = SimilarCaseQuery(
            problem_description=request.problem_description.strip(),
            product_code=request.product_code,
            customer_name=request.customer_name,
            batch_number=request.batch_number,
            symptoms=tuple(request.symptoms or ()),
            failure_mode=request.failure_mode,
            root_cause_category=request.root_cause_category,
            problem_category=request.problem_category,
            branch_code=request.branch_code,
        )

        raw_candidates = self._repository.fetch_similar_case_candidates(
            problem_description=query.problem_description,
            product_code=query.product_code,
            symptoms=list(query.symptoms),
            branch_code=query.branch_code,
            exclude_plan_id=request.exclude_plan_id,
        )
        candidates = [
            IndexedCaseCandidate(
                plan_id=item["plan_id"],
                plan_code=item["plan_code"],
                search_text=item["search_text"],
                product_code=item.get("product_code"),
                failure_mode=item.get("failure_mode"),
                root_cause_category=item.get("root_cause_category"),
                symptom_tags=item.get("symptom_tags") or [],
                problem_summary=item.get("problem_summary") or "",
                root_cause=item.get("root_cause"),
                effectiveness_status=item.get("effectiveness_status"),
                closed_at=item.get("closed_at"),
                effective_actions=item.get("effective_actions") or [],
                branch_code=item.get("branch_code"),
            )
            for item in raw_candidates
        ]

        similar_cases = self._decision_log.enrich_ranked_cases(query, candidates)
        recurrence = self._scoring.recurrence_signals(query, candidates)

        return {
            "similar_cases": similar_cases,
            "recurrence_signals": recurrence,
            "suggested_focus_areas": self._scoring.suggested_focus_areas(similar_cases),
            "similar_cases_decision_log": self._decision_log.build_from_ranked_cases(
                query,
                similar_cases,
            ),
        }


class GetPlanSimilarCasesUseCase:
    def __init__(
        self,
        plan_repository: PlanDetailReader,
        search_similar_cases: SearchSimilarCasesUseCase,
    ) -> None:
        self._plan_repository = plan_repository
        self._search_similar_cases = search_similar_cases

    def execute(self, plan_id: str) -> dict[str, Any] | None:
        detail = self._plan_repository.get_plan_detail(plan_id)
        if not detail:
            return None

        plan = detail.get("plan") or {}
        five_whys = detail.get("five_whys") or {}
        problem_description = (
            (plan.get("reported_problem") or "").strip()
            or (plan.get("title") or "").strip()
        )
        if not problem_description:
            raise ValueError("Plano sem descrição suficiente para buscar casos similares.")

        return self._search_similar_cases.execute(
            SimilarCasesRequest(
                problem_description=problem_description,
                product_code=plan.get("product_code"),
                customer_name=plan.get("customer_name"),
                batch_number=plan.get("batch_number"),
                symptoms=list(plan.get("symptom_tags") or []),
                failure_mode=plan.get("failure_mode"),
                root_cause_category=plan.get("root_cause_category") or five_whys.get("root_cause"),
                problem_category=plan.get("problem_category"),
                branch_code=plan.get("branch_code"),
                exclude_plan_id=plan_id,
            )
        )


class SolutionPatternsRepository(Protocol):
    def list_solution_patterns(
        self,
        *,
        problem_category: str | None = None,
        failure_mode: str | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]: ...

    def upsert_solution_pattern_from_plan(self, plan_id: str) -> dict[str, Any] | None: ...


class ListSolutionPatternsUseCase:
    def __init__(self, repository: SolutionPatternsRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        problem_category: str | None = None,
        failure_mode: str | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        return self._repository.list_solution_patterns(
            problem_category=problem_category,
            failure_mode=failure_mode,
            q=q,
            page=page,
            page_size=page_size,
        )


class PromoteSolutionPatternFromPlanUseCase:
    def __init__(self, repository: SolutionPatternsRepository) -> None:
        self._repository = repository

    def execute(self, plan_id: str) -> dict[str, Any] | None:
        return self._repository.upsert_solution_pattern_from_plan(plan_id)
