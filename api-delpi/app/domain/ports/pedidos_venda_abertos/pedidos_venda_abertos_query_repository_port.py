from __future__ import annotations

from typing import Protocol


class PedidosVendaAbertosQueryRepositoryPort(Protocol):
    def list_open_orders(self) -> tuple[list[dict], dict]: ...
