from app.application.use_cases.commercial.get_rol_target_pct_use_case import GetRolTargetPctUseCase
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import FinancialRepository


DEFAULT_HEAD_OFFICE_TARGET = 1.0
DEFAULT_BRANCH_TARGET = 1.0


def build_get_head_office_rol_target_pct_use_case() -> GetRolTargetPctUseCase:
    financial_query_repository = FinancialRepository()

    return GetRolTargetPctUseCase(
        financial_query_repository=financial_query_repository,
        target_value=DEFAULT_HEAD_OFFICE_TARGET,
    )


def build_get_branch_rol_target_pct_use_case() -> GetRolTargetPctUseCase:
    financial_query_repository = FinancialRepository()

    return GetRolTargetPctUseCase(
        financial_query_repository=financial_query_repository,
        target_value=DEFAULT_BRANCH_TARGET,
    )