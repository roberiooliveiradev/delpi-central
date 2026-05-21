from si_app.application.services.commercial.commercial_metrics_snapshot_service import (
    CommercialMetricsSnapshotService,
)
from si_app.application.use_cases.commercial.get_rol_target_pct_use_case import GetRolTargetPctUseCase
from si_app.infrastructure.persistence.totvs.financial_repositories.financial_repository import FinancialRepository
from si_app.application.use_cases.commercial.get_sales_conversion_rate_use_case import GetSalesConversionRateUseCase
from si_app.infrastructure.persistence.totvs.commercial_repositories.sales_conversion_rate_repository import SalesConversionRateRepository
from si_app.application.use_cases.commercial.get_new_clients_average_use_case import GetNewClientsAverageUseCase
from si_app.infrastructure.persistence.totvs.commercial_repositories.new_clients_average_repository import NewClientsAverageRepository
from si_app.application.use_cases.commercial.get_new_clients_rol_pct_use_case import GetNewClientsRolPctUseCase
from si_app.infrastructure.persistence.totvs.commercial_repositories.new_clients_rol_pct_repository import NewClientsRolPctRepository
from si_app.infrastructure.providers.strategic_indicators.commercial_indicators_snapshot_provider import (
    CommercialIndicatorsSnapshotProvider,
)

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
    return GetSalesConversionRateUseCase(
        sales_conversion_rate_repository=SalesConversionRateRepository()
    )


def build_get_new_clients_average_use_case() -> GetNewClientsAverageUseCase:
    return GetNewClientsAverageUseCase(
        new_clients_average_repository=NewClientsAverageRepository()
    )


def build_get_new_clients_rol_pct_use_case() -> GetNewClientsRolPctUseCase:
    return GetNewClientsRolPctUseCase(
        new_clients_rol_pct_repository=NewClientsRolPctRepository()
    )


def build_commercial_metrics_snapshot_service() -> CommercialMetricsSnapshotService:
    return CommercialMetricsSnapshotService(
        head_office_rol_target_use_case=build_get_head_office_rol_target_pct_use_case(),
        branch_rol_target_use_case=build_get_branch_rol_target_pct_use_case(),
        sales_conversion_rate_use_case=build_get_sales_conversion_rate_use_case(),
        new_clients_rol_pct_use_case=build_get_new_clients_rol_pct_use_case(),
    )


def build_commercial_indicators_snapshot_provider() -> CommercialIndicatorsSnapshotProvider:
    return CommercialIndicatorsSnapshotProvider(
        commercial_metrics_snapshot_service=build_commercial_metrics_snapshot_service(),
    )