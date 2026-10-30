"""Busca/listagem paginada de OPs da Auditoria de Consumo (GLPI #1353).

Read-only e leve por contrato: uma query de contagem + uma query de página
(SC2×SB1 com EXISTS SH6/SH8 apenas quando filtrado). Não calcula o detalhe
de nenhuma OP — esse trabalho pertence ao endpoint de detalhe.
"""

from __future__ import annotations

from app.application.dto.supplies.search_consumption_audit_orders_request import (
    SearchConsumptionAuditOrdersRequest,
)
from app.application.models.page import Page
from app.domain.ports.production.consumption_audit_repository_port import (
    ConsumptionAuditRepositoryPort,
)
from app.infrastructure.persistence.totvs.pagination import paginate


class SearchConsumptionAuditOrdersUseCase:
    def __init__(self, repository: ConsumptionAuditRepositoryPort):
        self._repository = repository

    def execute(self, request: SearchConsumptionAuditOrdersRequest) -> Page:
        paging = paginate(request.page, request.page_size)
        filters = {
            "branch": request.branch,
            "search": request.search,
            "product": request.product,
            "date_type": request.date_type,
            "period_start": request.period_start,
            "period_end": request.period_end,
            "status": request.status,
            "work_center": request.work_center,
            "operation": request.operation,
        }
        total = self._repository.count_orders(**filters)
        items = self._repository.search_orders(
            **filters,
            offset=paging["offset"],
            limit=paging["page_size"],
        )
        return Page(
            items=items,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"],
        )
