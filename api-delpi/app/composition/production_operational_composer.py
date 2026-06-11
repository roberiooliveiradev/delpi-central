from app.application.use_cases.production.get_production_consumption_top_items_use_case import (
    GetProductionConsumptionTopItemsUseCase,
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
