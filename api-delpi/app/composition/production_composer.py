import os

from app.application.use_cases.production.get_direct_labor_cost_pct_use_case import GetDirectLaborCostPctUseCase
from app.application.use_cases.production.get_production_cost_pct_use_case import GetProductionCostPctUseCase
from app.application.use_cases.production.get_depreciation_pct_use_case import GetDepreciationPctUseCase

from app.application.use_cases.production.get_overall_equipment_effectiveness_pct_use_case import GetOverallEquipmentEffectivenessPctUseCase

from app.infrastructure.persistence.google_sheets.production.direct_labor_repository import DirectLaborRepository
from app.infrastructure.persistence.google_sheets.production.production_cost_repository import ProductionCostRepository
from app.infrastructure.persistence.google_sheets.production.depreciation_repository import DepreciationRepository

from app.infrastructure.persistence.totvs.production_repositories.overall_equipment_effectiveness_repository import OverallEquipmentEffectivenessRepository

from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import FinancialRepository

from app.application.use_cases.production.get_on_time_delivery_pct_use_case import GetOnTimeDeliveryPctUseCase
from app.infrastructure.persistence.totvs.production_repositories.on_time_delivery_repository import OnTimeDeliveryRepository




DEFAULT_PRODUCTION_SHEET_ID = "1UM3g5QPixVJitlryNg8xaa34syjYTzT6ydaVVon5_Lw"
DEFAULT_DIRECT_LABOR_SHEET_GID = "1525246844"
DEFAULT_PRODUCTION_COST_SHEET_GID = "1959625411"
DEFAULT_DEPRECIATION_SHEET_GID = "594516707"
DEFAULT_GOOGLE_SHEETS_TIMEOUT = 10


def _build_direct_labor_repository() -> DirectLaborRepository:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    sheet_id = os.getenv("DIRECT_LABOR_SHEET_ID", DEFAULT_PRODUCTION_SHEET_ID)
    gid = os.getenv("DIRECT_LABOR_SHEET_GID", DEFAULT_DIRECT_LABOR_SHEET_GID)

    client = GoogleSheetsClient(timeout=timeout)

    return DirectLaborRepository(
        client=client,
        sheet_id=sheet_id,
        gid=gid,
    )


def _build_production_cost_repository() -> ProductionCostRepository:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    sheet_id = os.getenv("PRODUCTION_COST_SHEET_ID", DEFAULT_PRODUCTION_SHEET_ID)
    gid = os.getenv("PRODUCTION_COST_SHEET_GID", DEFAULT_PRODUCTION_COST_SHEET_GID)

    client = GoogleSheetsClient(timeout=timeout)

    return ProductionCostRepository(
        client=client,
        sheet_id=sheet_id,
        gid=gid,
    )


def _build_depreciation_repository() -> DepreciationRepository:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    sheet_id = os.getenv("DEPRECIATION_SHEET_ID", DEFAULT_PRODUCTION_SHEET_ID)
    gid = os.getenv("DEPRECIATION_SHEET_GID", DEFAULT_DEPRECIATION_SHEET_GID)

    client = GoogleSheetsClient(timeout=timeout)

    return DepreciationRepository(
        client=client,
        sheet_id=sheet_id,
        gid=gid,
    )


def build_get_direct_labor_cost_pct_use_case() -> GetDirectLaborCostPctUseCase:
    direct_labor_repository = _build_direct_labor_repository()
    financial_query_repository = FinancialRepository()

    return GetDirectLaborCostPctUseCase(
        direct_labor_repository=direct_labor_repository,
        financial_query_repository=financial_query_repository,
    )


def build_get_production_cost_pct_use_case() -> GetProductionCostPctUseCase:
    production_cost_repository = _build_production_cost_repository()
    financial_query_repository = FinancialRepository()

    return GetProductionCostPctUseCase(
        production_cost_repository=production_cost_repository,
        financial_query_repository=financial_query_repository,
    )


def build_get_depreciation_pct_use_case() -> GetDepreciationPctUseCase:
    depreciation_repository = _build_depreciation_repository()
    financial_query_repository = FinancialRepository()

    return GetDepreciationPctUseCase(
        depreciation_repository=depreciation_repository,
        financial_query_repository=financial_query_repository,
    )


def build_get_overall_equipment_effectiveness_pct_use_case() -> GetOverallEquipmentEffectivenessPctUseCase:
    overall_equipment_effectiveness_repository = OverallEquipmentEffectivenessRepository()

    return GetOverallEquipmentEffectivenessPctUseCase(
        overall_equipment_effectiveness_repository=overall_equipment_effectiveness_repository
    )


def build_get_on_time_delivery_pct_use_case() -> GetOnTimeDeliveryPctUseCase:
    on_time_delivery_repository = OnTimeDeliveryRepository()

    return GetOnTimeDeliveryPctUseCase(
        on_time_delivery_repository=on_time_delivery_repository
    )