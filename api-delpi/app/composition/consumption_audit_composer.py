"""Composer — Auditoria de Consumo OP × operação (GLPI #1353)."""

from __future__ import annotations

from app.application.use_cases.supplies.get_consumption_audit_order_use_case import (
    GetConsumptionAuditOrderUseCase,
)
from app.infrastructure.persistence.totvs.production_repositories.consumption_audit_repository import (
    ConsumptionAuditRepository,
)


def build_get_consumption_audit_order_use_case() -> GetConsumptionAuditOrderUseCase:
    return GetConsumptionAuditOrderUseCase(ConsumptionAuditRepository())
