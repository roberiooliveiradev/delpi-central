from app.application.use_cases.production.get_production_allocation_gaps_use_case import (
    GetProductionAllocationGapsUseCase,
)
from app.application.use_cases.production.get_production_consumption_by_item_use_case import (
    GetProductionConsumptionByItemUseCase,
)
from app.application.use_cases.production.get_production_consumption_top_items_use_case import (
    GetProductionConsumptionTopItemsUseCase,
)
from app.application.use_cases.production.get_production_consumption_top_items_by_work_center_use_case import (
    GetProductionConsumptionTopItemsByWorkCenterUseCase,
)
from app.application.use_cases.production.get_production_consumption_top_items_validated_use_case import (
    GetProductionConsumptionTopItemsValidatedUseCase,
)
from app.application.use_cases.production.get_production_orders_finished_without_consumption_use_case import (
    GetProductionOrdersFinishedWithoutConsumptionUseCase,
)
from app.application.use_cases.production.get_production_orders_finished_use_case import (
    GetProductionOrdersFinishedUseCase,
)
from app.application.use_cases.production.get_production_orders_open_use_case import (
    GetProductionOrdersOpenUseCase,
)
from app.application.use_cases.production.get_production_work_center_average_planned_time_use_case import (
    GetProductionWorkCenterAveragePlannedTimeUseCase,
)
from app.application.use_cases.production.get_production_work_center_order_summary_use_case import (
    GetProductionWorkCenterOrderSummaryUseCase,
)
from app.application.use_cases.production.get_production_losses_records_use_case import (
    GetProductionLossesRecordsUseCase,
)
from app.application.use_cases.production.get_production_losses_top_materials_use_case import (
    GetProductionLossesTopMaterialsUseCase,
)
from app.application.use_cases.production.get_production_schedule_today_use_case import (
    GetProductionScheduleTodayUseCase,
)
from app.application.use_cases.purchases.get_purchases_top_products_use_case import (
    GetPurchasesTopProductsUseCase,
)
from app.infrastructure.persistence.totvs.production_repositories.production_consumption_repository import (
    ProductionConsumptionRepository,
)
from app.infrastructure.persistence.totvs.production_repositories.production_losses_repository import (
    ProductionLossesRepository,
)
from app.infrastructure.persistence.totvs.production_repositories.production_orders_repository import (
    ProductionOrdersRepository,
)
from app.infrastructure.persistence.totvs.production_repositories.production_work_centers_repository import (
    ProductionWorkCentersRepository,
)
from app.infrastructure.persistence.totvs.production_repositories.production_schedule_repository import (
    ProductionScheduleRepository,
)
from app.infrastructure.persistence.totvs.purchases_repositories.purchases_ranking_repository import (
    PurchasesRankingRepository,
)


def build_get_production_consumption_top_items_use_case() -> GetProductionConsumptionTopItemsUseCase:
    return GetProductionConsumptionTopItemsUseCase(ProductionConsumptionRepository())


def build_get_production_losses_records_use_case() -> GetProductionLossesRecordsUseCase:
    return GetProductionLossesRecordsUseCase(ProductionLossesRepository())


def build_get_production_losses_top_materials_use_case() -> GetProductionLossesTopMaterialsUseCase:
    return GetProductionLossesTopMaterialsUseCase(ProductionLossesRepository())


def build_get_production_schedule_today_use_case() -> GetProductionScheduleTodayUseCase:
    return GetProductionScheduleTodayUseCase(ProductionScheduleRepository())


def build_get_purchases_top_products_use_case() -> GetPurchasesTopProductsUseCase:
    return GetPurchasesTopProductsUseCase(PurchasesRankingRepository())


def build_get_production_orders_open_use_case() -> GetProductionOrdersOpenUseCase:
    return GetProductionOrdersOpenUseCase(ProductionOrdersRepository())


def build_get_production_orders_finished_use_case() -> GetProductionOrdersFinishedUseCase:
    return GetProductionOrdersFinishedUseCase(ProductionOrdersRepository())


def build_get_production_work_center_order_summary_use_case() -> (
    GetProductionWorkCenterOrderSummaryUseCase
):
    return GetProductionWorkCenterOrderSummaryUseCase(ProductionWorkCentersRepository())


def build_get_production_consumption_top_items_by_work_center_use_case() -> (
    GetProductionConsumptionTopItemsByWorkCenterUseCase
):
    return GetProductionConsumptionTopItemsByWorkCenterUseCase(ProductionConsumptionRepository())


def build_get_production_consumption_top_items_validated_use_case() -> (
    GetProductionConsumptionTopItemsValidatedUseCase
):
    return GetProductionConsumptionTopItemsValidatedUseCase(ProductionConsumptionRepository())


def build_get_production_allocation_gaps_use_case() -> GetProductionAllocationGapsUseCase:
    return GetProductionAllocationGapsUseCase(ProductionOrdersRepository())


def build_get_production_orders_finished_without_consumption_use_case() -> (
    GetProductionOrdersFinishedWithoutConsumptionUseCase
):
    return GetProductionOrdersFinishedWithoutConsumptionUseCase(ProductionOrdersRepository())


def build_get_production_work_center_average_planned_time_use_case() -> (
    GetProductionWorkCenterAveragePlannedTimeUseCase
):
    return GetProductionWorkCenterAveragePlannedTimeUseCase(ProductionWorkCentersRepository())


def build_get_production_consumption_by_item_use_case() -> (
    GetProductionConsumptionByItemUseCase
):
    return GetProductionConsumptionByItemUseCase(ProductionConsumptionRepository())
