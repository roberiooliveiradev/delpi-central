from __future__ import annotations

from typing import Protocol, Sequence


class PedidosVendaAbertosQueryRepositoryPort(Protocol):
    def list_open_orders(self) -> tuple[list[dict], dict]: ...

    def list_open_orders_for_customer(
        self,
        customer_code: str,
        customer_store: str,
    ) -> tuple[list[dict], dict]: ...

    def aggregate_customer_open_order_metrics(
        self,
        customer_keys: Sequence[tuple[str, str]] | None = None,
    ) -> list[dict]: ...
