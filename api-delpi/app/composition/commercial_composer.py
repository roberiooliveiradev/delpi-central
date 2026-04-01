from app.application.use_cases.commercial.get_rol_target_pct_use_case import GetRolTargetPctUseCase
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import FinancialRepository
from app.application.use_cases.commercial.get_sales_conversion_rate_use_case import GetSalesConversionRateUseCase
from app.infrastructure.persistence.totvs.commercial_repositories.sales_conversion_rate_repository import SalesConversionRateRepository
from app.application.use_cases.commercial.get_new_clients_average_use_case import GetNewClientsAverageUseCase
from app.infrastructure.persistence.totvs.commercial_repositories.new_clients_average_repository import NewClientsAverageRepository
from app.application.use_cases.commercial.get_new_clients_rol_pct_use_case import GetNewClientsRolPctUseCase
from app.infrastructure.persistence.totvs.commercial_repositories.new_clients_rol_pct_repository import NewClientsRolPctRepository

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

def build_get_sales_conversion_rate_use_case() -> GetSalesConversionRateUseCase:
    sales_conversion_rate_repository = SalesConversionRateRepository()

    return GetSalesConversionRateUseCase(
        sales_conversion_rate_repository=sales_conversion_rate_repository
    )


def build_get_new_clients_average_use_case() -> GetNewClientsAverageUseCase:
    new_clients_average_repository = NewClientsAverageRepository()

    return GetNewClientsAverageUseCase(
        new_clients_average_repository=new_clients_average_repository
    )


def build_get_new_clients_rol_pct_use_case() -> GetNewClientsRolPctUseCase:
    repository = NewClientsRolPctRepository()

    return GetNewClientsRolPctUseCase(
        new_clients_rol_pct_repository=repository
    )