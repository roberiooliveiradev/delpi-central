"""Composer — Auditoria de Consumo OP × operação (GLPI #1353)."""

from __future__ import annotations

from app.application.use_cases.supplies.get_consumption_audit_comparison_use_case import (
    GetConsumptionAuditComparisonUseCase,
)
from app.application.use_cases.supplies.get_consumption_audit_order_use_case import (
    GetConsumptionAuditOrderUseCase,
)
from app.application.use_cases.supplies.search_consumption_audit_orders_use_case import (
    SearchConsumptionAuditOrdersUseCase,
)
from app.infrastructure.persistence.totvs.production_repositories.consumption_audit_repository import (
    ConsumptionAuditRepository,
)


def build_get_consumption_audit_order_use_case() -> GetConsumptionAuditOrderUseCase:
    return GetConsumptionAuditOrderUseCase(ConsumptionAuditRepository())


def build_search_consumption_audit_orders_use_case() -> SearchConsumptionAuditOrdersUseCase:
    return SearchConsumptionAuditOrdersUseCase(ConsumptionAuditRepository())


def build_get_consumption_audit_comparison_use_case() -> GetConsumptionAuditComparisonUseCase:
    return GetConsumptionAuditComparisonUseCase(
        build_get_consumption_audit_order_use_case()
    )
