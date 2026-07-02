from __future__ import annotations

from abc import ABC, abstractmethod


class ProductionOrderCustomerRepositoryPort(ABC):
    """Rastreio do cliente a partir da OP (SC2 → SC5 → SA1)."""

    @abstractmethod
    def fetch_order_customer(
        self,
        *,
        production_order: str,
        branch: str | None = None,
    ) -> dict | None:
        """Retorna dados do cliente amarrado à OP via pedido de venda, ou None."""
        raise NotImplementedError
