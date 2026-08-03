"""Composition — ordens de produção."""

from __future__ import annotations

from app.application.use_cases.production.get_production_pcp_orders_use_cases import (
    GetProductionPcpOrdersItemsUseCase,
    GetProductionPcpOrdersRankingUseCase,
    GetProductionPcpOrdersSummaryUseCase,
)
from app.infrastructure.persistence.totvs.production.pcp_orders_repository import (
    PcpOrdersRepository,
)


def build_get_production_pcp_orders_summary_use_case() -> (
    GetProductionPcpOrdersSummaryUseCase
):
    return GetProductionPcpOrdersSummaryUseCase(repository=PcpOrdersRepository())


def build_get_production_pcp_orders_items_use_case() -> GetProductionPcpOrdersItemsUseCase:
    return GetProductionPcpOrdersItemsUseCase(repository=PcpOrdersRepository())


def build_get_production_pcp_orders_ranking_use_case() -> (
    GetProductionPcpOrdersRankingUseCase
):
    return GetProductionPcpOrdersRankingUseCase(repository=PcpOrdersRepository())
