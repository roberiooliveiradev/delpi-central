from si_app.application.services.commercial.commercial_metrics_snapshot_service import (
    CommercialMetricsSnapshotService,
)
from si_app.application.use_cases.commercial.get_rol_target_pct_use_case import GetRolTargetPctUseCase
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway
from si_app.application.use_cases.commercial.get_sales_conversion_rate_use_case import GetSalesConversionRateUseCase
from si_app.application.use_cases.commercial.get_new_business_rol_pct_use_case import (
    GetNewBusinessRolPctUseCase,
)
from si_app.application.use_cases.commercial.get_sales_order_otd_use_case import (
    GetSalesOrderOtdUseCase,
)
from si_app.infrastructure.providers.strategic_indicators.commercial_indicators_snapshot_provider import (
    CommercialIndicatorsSnapshotProvider,
)
from si_app.infrastructure.gateways.delpi_commercial_gateway import (
    DelpiNewBusinessRolPctGateway,
    DelpiSalesConversionRateGateway,
    DelpiSalesOrderOtdGateway,
)
from delpi_api_client import DelpiApiClient

DEFAULT_HEAD_OFFICE_TARGET = 1.0
DEFAULT_BRANCH_TARGET = 1.0

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def build_get_head_office_rol_target_pct_use_case() -> GetRolTargetPctUseCase:
    return GetRolTargetPctUseCase(
        financial_query_repository=DelpiFinancialGateway(_get_delpi_client()),
        target_value=DEFAULT_HEAD_OFFICE_TARGET,
    )


def build_get_branch_rol_target_pct_use_case() -> GetRolTargetPctUseCase:
    return GetRolTargetPctUseCase(
        financial_query_repository=DelpiFinancialGateway(_get_delpi_client()),
        target_value=DEFAULT_BRANCH_TARGET,
    )


def build_get_sales_conversion_rate_use_case() -> GetSalesConversionRateUseCase:
    return GetSalesConversionRateUseCase(
        sales_conversion_rate_repository=DelpiSalesConversionRateGateway(_get_delpi_client())
    )


def build_get_new_business_rol_pct_use_case() -> GetNewBusinessRolPctUseCase:
    return GetNewBusinessRolPctUseCase(
        new_business_rol_pct_repository=DelpiNewBusinessRolPctGateway(_get_delpi_client())
    )


def build_get_sales_order_otd_use_case() -> GetSalesOrderOtdUseCase:
    return GetSalesOrderOtdUseCase(
        sales_order_otd_repository=DelpiSalesOrderOtdGateway(_get_delpi_client())
    )


def build_commercial_metrics_snapshot_service() -> CommercialMetricsSnapshotService:
    return CommercialMetricsSnapshotService(
        head_office_rol_target_use_case=build_get_head_office_rol_target_pct_use_case(),
        branch_rol_target_use_case=build_get_branch_rol_target_pct_use_case(),
        sales_conversion_rate_use_case=build_get_sales_conversion_rate_use_case(),
        new_business_rol_pct_use_case=build_get_new_business_rol_pct_use_case(),
        sales_order_otd_use_case=build_get_sales_order_otd_use_case(),
    )


def build_commercial_indicators_snapshot_provider() -> CommercialIndicatorsSnapshotProvider:
    return CommercialIndicatorsSnapshotProvider(
        commercial_metrics_snapshot_service=build_commercial_metrics_snapshot_service(),
    )
