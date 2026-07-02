from __future__ import annotations

from app.domain.ports.production.production_order_customer_repository_port import (
    ProductionOrderCustomerRepositoryPort,
)


class GetOrderCustomerByOpUseCase:
    """Rastreia o cliente amarrado à OP via pedido de venda (quando existir)."""

    def __init__(self, repository: ProductionOrderCustomerRepositoryPort):
        self._repository = repository

    def execute(self, *, production_order: str, branch: str | None = None) -> dict | None:
        order = (production_order or "").strip()
        if not order:
            return None
        try:
            return self._repository.fetch_order_customer(
                production_order=order,
                branch=branch,
            )
        except Exception:
            # Rastreio é best-effort: falha no TOTVS não deve quebrar o certificado.
            return None
