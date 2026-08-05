from __future__ import annotations

from app.application.services.planejamento_orcamentario.document_storage import (
    BudgetDocumentStorage,
)
from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetPlanningUseCases,
)
from app.application.use_cases.planejamento_orcamentario.budget_responsibility_use_cases import (
    BudgetResponsibilityUseCases,
)
from app.application.use_cases.planejamento_orcamentario.capex_attachment_use_cases import (
    CapexAttachmentUseCases,
)
from app.application.use_cases.planejamento_orcamentario.capex_category_use_cases import (
    CapexCategoryUseCases,
)
from app.application.use_cases.planejamento_orcamentario.capex_investment_use_cases import (
    CapexInvestmentUseCases,
)
from app.application.use_cases.planejamento_orcamentario.capex_consolidation_use_cases import (
    CapexConsolidationUseCases,
)
from app.application.use_cases.planejamento_orcamentario.capex_plan_use_cases import (
    CapexPlanUseCases,
)
from app.application.use_cases.planejamento_orcamentario.personnel_plan_use_cases import (
    PersonnelPlanUseCases,
)
from app.infrastructure.persistence.plugins.repositories.planejamento_orcamentario.postgres_budget_planning_repository import (
    PostgresBudgetPlanningRepository,
)


def build_budget_planning_repository() -> PostgresBudgetPlanningRepository:
    return PostgresBudgetPlanningRepository()


def build_budget_document_storage() -> BudgetDocumentStorage:
    return BudgetDocumentStorage()


def build_budget_planning_use_cases() -> BudgetPlanningUseCases:
    return BudgetPlanningUseCases(
        repository=build_budget_planning_repository(),
        storage=build_budget_document_storage(),
    )


def build_budget_responsibility_use_cases() -> BudgetResponsibilityUseCases:
    return BudgetResponsibilityUseCases(
        repository=build_budget_planning_repository(),
    )


def build_capex_category_use_cases() -> CapexCategoryUseCases:
    return CapexCategoryUseCases(
        repository=build_budget_planning_repository(),
    )


def build_capex_investment_use_cases() -> CapexInvestmentUseCases:
    return CapexInvestmentUseCases(
        repository=build_budget_planning_repository(),
    )


def build_capex_attachment_use_cases() -> CapexAttachmentUseCases:
    return CapexAttachmentUseCases(
        repository=build_budget_planning_repository(),
        storage=build_budget_document_storage(),
    )


def build_capex_plan_use_cases() -> CapexPlanUseCases:
    return CapexPlanUseCases(
        repository=build_budget_planning_repository(),
    )


def build_capex_consolidation_use_cases() -> CapexConsolidationUseCases:
    return CapexConsolidationUseCases(
        repository=build_budget_planning_repository(),
    )


def build_personnel_plan_use_cases() -> PersonnelPlanUseCases:
    return PersonnelPlanUseCases(
        repository=build_budget_planning_repository(),
    )
