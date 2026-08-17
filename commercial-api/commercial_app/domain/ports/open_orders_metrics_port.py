from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class CustomerOpenOrderMetric:
    customer_code: str
    customer_store: str
    customer_name: str | None
    open_value: float
    has_overdue: bool


class OpenOrdersMetricsPort(ABC):
    @abstractmethod
    def list_customer_metrics(
        self,
        customer_keys: Sequence[tuple[str, str]] | None = None,
    ) -> list[CustomerOpenOrderMetric]:
        """Métricas agregadas de pedidos em aberto por cliente.

        customer_keys=None → universo completo (todos com pedido aberto).
        """
        raise NotImplementedError
