import os

from app.application.services.production.production_metrics_snapshot_service import (
    ProductionMetricsSnapshotService,
)
from app.application.use_cases.production.get_depreciation_pct_use_case import (
    GetDepreciationPctUseCase,
)
from app.application.use_cases.production.get_direct_labor_cost_pct_use_case import (
    GetDirectLaborCostPctUseCase,
)
from app.application.use_cases.production.get_on_time_delivery_pct_use_case import (
    GetOnTimeDeliveryPctUseCase,
)
from app.application.use_cases.production.get_overall_equipment_effectiveness_pct_use_case import (
    GetOverallEquipmentEffectivenessPctUseCase,
)
from app.application.use_cases.production.get_production_cost_pct_use_case import (
    GetProductionCostPctUseCase,
)
from app.infrastructure.persistence.google_sheets.production.depreciation_repository import (
    DepreciationRepository,
)
from app.infrastructure.persistence.google_sheets.production.direct_labor_repository import (
    DirectLaborRepository,
)
from app.infrastructure.persistence.google_sheets.production.production_cost_repository import (
    ProductionCostRepository,
)
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)
from app.infrastructure.persistence.totvs.production_repositories.on_time_delivery_repository import (
    OnTimeDeliveryRepository,
)
from app.infrastructure.persistence.totvs.production_repositories.overall_equipment_effectiveness_repository import (
    OverallEquipmentEffectivenessRepository,
)
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)

DEFAULT_PRODUCTION_SHEET_ID = "1UM3g5QPixVJitlryNg8xaa34syjYTzT6ydaVVon5_Lw"
DEFAULT_DIRECT_LABOR_SHEET_GID = "1525246844"
DEFAULT_PRODUCTION_COST_SHEET_GID = "1959625411"
DEFAULT_DEPRECIATION_SHEET_GID = "594516707"
DEFAULT_GOOGLE_SHEETS_TIMEOUT = 10


def _build_google_sheets_client() -> GoogleSheetsClient:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    return GoogleSheetsClient(timeout=timeout)


def _build_direct_labor_repository(client: GoogleSheetsClient) -> DirectLaborRepository:
    sheet_id = os.getenv("DIRECT_LABOR_SHEET_ID", DEFAULT_PRODUCTION_SHEET_ID)
    gid = os.getenv("DIRECT_LABOR_SHEET_GID", DEFAULT_DIRECT_LABOR_SHEET_GID)
    return DirectLaborRepository(client=client, sheet_id=sheet_id, gid=gid)


def _build_production_cost_repository(client: GoogleSheetsClient) -> ProductionCostRepository:
    sheet_id = os.getenv("PRODUCTION_COST_SHEET_ID", DEFAULT_PRODUCTION_SHEET_ID)
    gid = os.getenv("PRODUCTION_COST_SHEET_GID", DEFAULT_PRODUCTION_COST_SHEET_GID)
    return ProductionCostRepository(client=client, sheet_id=sheet_id, gid=gid)


def _build_depreciation_repository(client: GoogleSheetsClient) -> DepreciationRepository:
    sheet_id = os.getenv("DEPRECIATION_SHEET_ID", DEFAULT_PRODUCTION_SHEET_ID)
    gid = os.getenv("DEPRECIATION_SHEET_GID", DEFAULT_DEPRECIATION_SHEET_GID)
    return DepreciationRepository(client=client, sheet_id=sheet_id, gid=gid)


def build_production_metrics_snapshot_service() -> ProductionMetricsSnapshotService:
    client = _build_google_sheets_client()

    return ProductionMetricsSnapshotService(
        direct_labor_repository=_build_direct_labor_repository(client),
        production_cost_repository=_build_production_cost_repository(client),
        depreciation_repository=_build_depreciation_repository(client),
        overall_equipment_effectiveness_repository=OverallEquipmentEffectivenessRepository(),
        on_time_delivery_repository=OnTimeDeliveryRepository(),
        financial_query_repository=FinancialRepository(),
    )


def build_get_direct_labor_cost_pct_use_case() -> GetDirectLaborCostPctUseCase:
    client = _build_google_sheets_client()
    return GetDirectLaborCostPctUseCase(
        direct_labor_repository=_build_direct_labor_repository(client),
        financial_query_repository=FinancialRepository(),
    )


def build_get_production_cost_pct_use_case() -> GetProductionCostPctUseCase:
    client = _build_google_sheets_client()
    return GetProductionCostPctUseCase(
        production_cost_repository=_build_production_cost_repository(client),
        financial_query_repository=FinancialRepository(),
    )


def build_get_depreciation_pct_use_case() -> GetDepreciationPctUseCase:
    client = _build_google_sheets_client()
    return GetDepreciationPctUseCase(
        depreciation_repository=_build_depreciation_repository(client),
        financial_query_repository=FinancialRepository(),
    )


def build_get_overall_equipment_effectiveness_pct_use_case() -> GetOverallEquipmentEffectivenessPctUseCase:
    return GetOverallEquipmentEffectivenessPctUseCase(
        overall_equipment_effectiveness_repository=OverallEquipmentEffectivenessRepository()
    )


def build_get_on_time_delivery_pct_use_case() -> GetOnTimeDeliveryPctUseCase:
    return GetOnTimeDeliveryPctUseCase(
        on_time_delivery_repository=OnTimeDeliveryRepository()
    )