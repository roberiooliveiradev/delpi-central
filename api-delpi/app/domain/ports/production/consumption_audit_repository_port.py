"""Port — leituras read-only da Auditoria de Consumo OP × operação (GLPI #1353)."""

from __future__ import annotations

from typing import Protocol, Sequence


class ConsumptionAuditRepositoryPort(Protocol):
    """Contrato mínimo consumido pelo use case de auditoria de consumo.

    Todas as leituras são ``SELECT`` parametrizadas no Protheus — nenhuma
    escrita, agregação especulativa ou regra derivada fora do Protheus.
    """

    def fetch_order(
        self, *, production_order: str, branch: str
    ) -> dict | None: ...

    def fetch_family_orders(
        self,
        *,
        order_number: str,
        branch: str,
        exclude_production_order: str,
    ) -> list[dict]: ...

    def fetch_commitments(
        self, *, production_order: str, branch: str
    ) -> list[dict]: ...

    def fetch_movements(
        self, *, production_order: str, branch: str
    ) -> list[dict]: ...

    def fetch_appointments(
        self, *, production_order: str, branch: str
    ) -> list[dict]: ...

    def fetch_operation_events(
        self, *, production_order: str, branch: str
    ) -> list[dict]: ...

    def fetch_allocations(
        self, *, production_order: str, branch: str
    ) -> list[dict]: ...

    def fetch_routing(
        self, *, product_code: str, branch: str
    ) -> list[dict]: ...

    def fetch_bom_components(
        self, *, product_code: str, branch: str, reference_date: str
    ) -> list[dict]: ...

    def fetch_product_metadata(
        self, *, codes: Sequence[str]
    ) -> dict[str, dict]: ...

    def fetch_parent_consumers(
        self, *, production_order: str, branch: str
    ) -> list[dict]: ...
