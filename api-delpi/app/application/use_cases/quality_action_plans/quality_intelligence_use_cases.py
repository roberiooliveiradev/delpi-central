from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.services.quality_action_plans.case_similarity_decision_log_service import (
    CaseSimilarityDecisionLogService,
)
from app.domain.services.quality_action_plans.case_similarity_embedding_service import (
    CaseSimilarityEmbeddingPort,
    CaseSimilarityEmbeddingService,
)
from app.domain.services.quality_action_plans.case_similarity_scoring_service import (
    CaseSimilarityScoringService,
    IndexedCaseCandidate,
    SimilarCaseQuery,
)
from app.domain.services.quality_action_plans.pac_quality_branch_service import (
    build_recurrence_key,
    validate_branch_code,
)
from app.domain.services.quality_action_plans.pac_recurrence_proactive_alert_service import (
    PacRecurrenceProactiveAlertService,
)


class CaseSimilarityIndexRepository(Protocol):
    def sync_case_similarity_index(self, plan_id: str) -> str | None: ...

    def update_search_embedding(self, plan_id: str, embedding: list[float]) -> None: ...


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
        query_embedding: list[float] | None = None,
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
    def __init__(
        self,
        repository: CaseSimilarityIndexRepository,
        embedding_gateway: CaseSimilarityEmbeddingPort | None = None,
    ) -> None:
        self._repository = repository
        self._embedding_gateway = embedding_gateway

    def execute(self, plan_id: str) -> None:
        search_text = self._repository.sync_case_similarity_index(plan_id)
        if not search_text or self._embedding_gateway is None:
            return

        embedding = CaseSimilarityEmbeddingService.embed_search_text(
            self._embedding_gateway,
            search_text,
        )
        if embedding:
            self._repository.update_search_embedding(plan_id, embedding)


class SearchSimilarCasesUseCase:
    def __init__(
        self,
        repository: SimilarCasesSearchRepository,
        scoring: CaseSimilarityScoringService | None = None,
        decision_log: CaseSimilarityDecisionLogService | None = None,
        embedding_gateway: CaseSimilarityEmbeddingPort | None = None,
    ) -> None:
        self._repository = repository
        self._scoring = scoring or CaseSimilarityScoringService()
        self._decision_log = decision_log or CaseSimilarityDecisionLogService(self._scoring)
        self._embedding_gateway = embedding_gateway

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

        query_embedding = None
        if self._embedding_gateway is not None:
            query_embedding = CaseSimilarityEmbeddingService.embed_search_text(
                self._embedding_gateway,
                query.problem_description,
            )

        raw_candidates = self._repository.fetch_similar_case_candidates(
            problem_description=query.problem_description,
            product_code=query.product_code,
            symptoms=list(query.symptoms),
            branch_code=query.branch_code,
            exclude_plan_id=request.exclude_plan_id,
            query_embedding=query_embedding,
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
                semantic_similarity=item.get("semantic_similarity"),
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


class RecurrenceOpeningRepository(Protocol):
    def fetch_recurrence_opening_stats(
        self,
        *,
        recurrence_key: str,
        branch_code: str | None = None,
        window_months: int = 12,
    ) -> dict[str, int]: ...


@dataclass(frozen=True)
class AssessRecurrenceOnOpeningRequest:
    problem_description: str
    product_code: str | None = None
    failure_mode: str | None = None
    branch_code: str | None = None
    symptoms: list[str] | None = None
    root_cause_category: str | None = None
    recurrence_key: str | None = None


class AssessRecurrenceOnOpeningUseCase:
    def __init__(
        self,
        repository: RecurrenceOpeningRepository,
        search_similar_cases: SearchSimilarCasesUseCase,
    ) -> None:
        self._repository = repository
        self._search_similar_cases = search_similar_cases

    def execute(self, request: AssessRecurrenceOnOpeningRequest) -> dict[str, Any]:
        if not request.problem_description.strip():
            raise ValueError("problem_description é obrigatório.")

        branch_code = validate_branch_code(request.branch_code, required=False)
        recurrence_key = build_recurrence_key(
            branch_code=branch_code,
            product_code=request.product_code,
            failure_mode=request.failure_mode,
            explicit=request.recurrence_key,
        )

        from app.domain.services.quality_action_plans.pac_recurrence_alert_content_service import (
            PacRecurrenceAlertContentService,
        )

        window_months = PacRecurrenceAlertContentService.window_months()
        stats = {"plans_in_window": 0, "open_plans": 0, "total_plans": 0}

        if recurrence_key:
            stats = self._repository.fetch_recurrence_opening_stats(
                recurrence_key=recurrence_key,
                branch_code=branch_code,
                window_months=window_months,
            )

        similar_result = self._search_similar_cases.execute(
            SimilarCasesRequest(
                problem_description=request.problem_description.strip(),
                product_code=request.product_code,
                failure_mode=request.failure_mode,
                branch_code=branch_code,
                symptoms=request.symptoms,
                root_cause_category=request.root_cause_category,
            )
        )
        recurrence_signals = similar_result.get("recurrence_signals") or {}

        if not recurrence_key and int(recurrence_signals.get("same_product") or 0) >= 2:
            stats = {
                **stats,
                "plans_in_window": max(
                    stats["plans_in_window"],
                    int(recurrence_signals.get("same_product") or 0),
                ),
                "total_plans": max(
                    stats["total_plans"],
                    int(recurrence_signals.get("same_product") or 0),
                ),
            }

        assessment = PacRecurrenceProactiveAlertService.build_assessment(
            recurrence_key=recurrence_key,
            plans_in_window=stats["plans_in_window"],
            open_plans=stats["open_plans"],
            total_plans=stats["total_plans"],
            recurrence_signals=recurrence_signals,
        )

        return {
            **assessment,
            "similar_cases_preview": (similar_result.get("similar_cases") or [])[:3],
            "similar_cases_decision_log": similar_result.get("similar_cases_decision_log"),
        }
