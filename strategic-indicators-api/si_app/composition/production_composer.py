from si_app.config import settings

from si_app.application.services.production.production_metrics_snapshot_service import (
    ProductionMetricsSnapshotService,
)
from si_app.application.use_cases.production.get_depreciation_pct_use_case import (
    GetDepreciationPctUseCase,
)
from si_app.application.use_cases.production.get_direct_labor_cost_pct_use_case import (
    GetDirectLaborCostPctUseCase,
)
from si_app.application.use_cases.production.get_on_time_delivery_pct_use_case import (
    GetOnTimeDeliveryPctUseCase,
)
from si_app.application.use_cases.production.get_overall_equipment_effectiveness_pct_use_case import (
    GetOverallEquipmentEffectivenessPctUseCase,
)
from si_app.application.use_cases.production.get_production_cost_pct_use_case import (
    GetProductionCostPctUseCase,
)
from si_app.infrastructure.persistence.google_sheets.production.depreciation_repository import (
    DepreciationRepository,
)
from si_app.infrastructure.persistence.google_sheets.production.direct_labor_repository import (
    DirectLaborRepository,
)
from si_app.infrastructure.persistence.google_sheets.production.production_cost_repository import (
    ProductionCostRepository,
)
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway
from si_app.infrastructure.gateways.delpi_production_gateway import (
    DelpiOeeGateway,
    DelpiOtdProductionGateway,
)
from si_app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)
from delpi_api_client import DelpiApiClient

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def _build_google_sheets_client() -> GoogleSheetsClient:
    return GoogleSheetsClient(timeout=int(settings.GOOGLE_SHEETS_TIMEOUT))


def _build_direct_labor_repository(
    client: GoogleSheetsClient,
) -> DirectLaborRepository:
    return DirectLaborRepository(
        client=client,
        sheet_id=settings.DIRECT_LABOR_SHEET_ID,
        gid=settings.DIRECT_LABOR_SHEET_GID,
    )


def _build_production_cost_repository(
    client: GoogleSheetsClient,
) -> ProductionCostRepository:
    return ProductionCostRepository(
        client=client,
        sheet_id=settings.PRODUCTION_COST_SHEET_ID,
        gid=settings.PRODUCTION_COST_SHEET_GID,
    )


def _build_depreciation_repository(
    client: GoogleSheetsClient,
) -> DepreciationRepository:
    return DepreciationRepository(
        client=client,
        sheet_id=settings.DEPRECIATION_SHEET_ID,
        gid=settings.DEPRECIATION_SHEET_GID,
    )


def build_production_metrics_snapshot_service() -> ProductionMetricsSnapshotService:
    client_gs = _build_google_sheets_client()
    delpi = _get_delpi_client()

    return ProductionMetricsSnapshotService(
        direct_labor_repository=_build_direct_labor_repository(client_gs),
        production_cost_repository=_build_production_cost_repository(client_gs),
        depreciation_repository=_build_depreciation_repository(client_gs),
        overall_equipment_effectiveness_repository=DelpiOeeGateway(delpi),
        on_time_delivery_repository=DelpiOtdProductionGateway(delpi),
        financial_query_repository=DelpiFinancialGateway(delpi),
    )


def build_get_direct_labor_cost_pct_use_case() -> GetDirectLaborCostPctUseCase:
    client_gs = _build_google_sheets_client()
    return GetDirectLaborCostPctUseCase(
        direct_labor_repository=_build_direct_labor_repository(client_gs),
        financial_query_repository=DelpiFinancialGateway(_get_delpi_client()),
    )


def build_get_production_cost_pct_use_case() -> GetProductionCostPctUseCase:
    client_gs = _build_google_sheets_client()
    return GetProductionCostPctUseCase(
        production_cost_repository=_build_production_cost_repository(client_gs),
        financial_query_repository=DelpiFinancialGateway(_get_delpi_client()),
    )


def build_get_depreciation_pct_use_case() -> GetDepreciationPctUseCase:
    client_gs = _build_google_sheets_client()
    return GetDepreciationPctUseCase(
        depreciation_repository=_build_depreciation_repository(client_gs),
        financial_query_repository=DelpiFinancialGateway(_get_delpi_client()),
    )


def build_get_overall_equipment_effectiveness_pct_use_case() -> GetOverallEquipmentEffectivenessPctUseCase:
    return GetOverallEquipmentEffectivenessPctUseCase(
        overall_equipment_effectiveness_repository=DelpiOeeGateway(_get_delpi_client())
    )


def build_get_on_time_delivery_pct_use_case() -> GetOnTimeDeliveryPctUseCase:
    return GetOnTimeDeliveryPctUseCase(
        on_time_delivery_repository=DelpiOtdProductionGateway(_get_delpi_client())
    )