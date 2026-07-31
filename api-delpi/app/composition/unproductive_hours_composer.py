"""Composition — horas improdutivas de produção."""

from __future__ import annotations

from app.application.use_cases.production.get_production_unproductive_hours_items_use_case import (
    GetProductionUnproductiveHoursItemsUseCase,
)
from app.application.use_cases.production.get_production_unproductive_hours_ranking_use_case import (
    GetProductionUnproductiveHoursRankingUseCase,
)
from app.application.use_cases.production.get_production_unproductive_hours_summary_use_case import (
    GetProductionUnproductiveHoursSummaryUseCase,
)
from app.infrastructure.persistence.totvs.production.unproductive_hours_repository import (
    UnproductiveHoursRepository,
)


def build_get_production_unproductive_hours_summary_use_case() -> (
    GetProductionUnproductiveHoursSummaryUseCase
):
    return GetProductionUnproductiveHoursSummaryUseCase(
        repository=UnproductiveHoursRepository()
    )


def build_get_production_unproductive_hours_items_use_case() -> (
    GetProductionUnproductiveHoursItemsUseCase
):
    return GetProductionUnproductiveHoursItemsUseCase(
        repository=UnproductiveHoursRepository()
    )


def build_get_production_unproductive_hours_ranking_use_case() -> (
    GetProductionUnproductiveHoursRankingUseCase
):
    return GetProductionUnproductiveHoursRankingUseCase(
        repository=UnproductiveHoursRepository()
    )
