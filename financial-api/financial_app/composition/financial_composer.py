from __future__ import annotations

from financial_app.application.services.cost_center_service import CostCenterService
from financial_app.application.services.delinquency_service import DelinquencyService
from financial_app.application.services.indicators_service import IndicatorsService
from financial_app.application.services.overview_service import OverviewService
from financial_app.application.services.subplugin_catalog_service import SubpluginCatalogService
from financial_app.domain.services.branch_access_service import BranchAccessService
from financial_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway
from financial_app.infrastructure.gateways.strategic_indicators_gateway import (
    StrategicIndicatorsGateway,
)


def build_catalog_service() -> SubpluginCatalogService:
    return SubpluginCatalogService()


def build_branch_access_service() -> BranchAccessService:
    return BranchAccessService()


def build_financial_gateway() -> DelpiFinancialGateway:
    return DelpiFinancialGateway()


def build_strategic_indicators_gateway() -> StrategicIndicatorsGateway:
    return StrategicIndicatorsGateway()


def build_delinquency_service(
    gateway: DelpiFinancialGateway | None = None,
) -> DelinquencyService:
    return DelinquencyService(
        gateway or build_financial_gateway(),
        branch_access=build_branch_access_service(),
    )


def build_cost_center_service(
    gateway: DelpiFinancialGateway | None = None,
) -> CostCenterService:
    return CostCenterService(
        gateway or build_financial_gateway(),
        branch_access=build_branch_access_service(),
    )


def build_indicators_service(
    gateway: StrategicIndicatorsGateway | None = None,
) -> IndicatorsService:
    return IndicatorsService(
        gateway or build_strategic_indicators_gateway(),
        branch_access=build_branch_access_service(),
    )


def build_overview_service(
    gateway: DelpiFinancialGateway | None = None,
    *,
    indicators_gateway: StrategicIndicatorsGateway | None = None,
) -> OverviewService:
    financial_gateway = gateway or build_financial_gateway()
    return OverviewService(
        financial_gateway,
        delinquency=build_delinquency_service(financial_gateway),
        cost_centers=build_cost_center_service(financial_gateway),
        indicators=build_indicators_service(indicators_gateway),
        branch_access=build_branch_access_service(),
    )
