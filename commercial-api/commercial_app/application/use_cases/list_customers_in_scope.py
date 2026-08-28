"""Lista clientes vinculados no escopo (Minha carteira) + métricas de aberto."""

from __future__ import annotations

import logging
from typing import Any

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.domain.entities.customers_in_scope import CustomersInScopeResult
from commercial_app.domain.entities.seller_portfolio import SellerCustomerAssignment
from commercial_app.domain.ports.open_orders_metrics_port import OpenOrdersMetricsPort
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.services.list_customers_in_scope_service import (
    ListCustomersInScopeService,
)
from commercial_app.domain.services.seller_portfolio_coverage_audit_service import (
    customer_coverage_key,
)

logger = logging.getLogger("commercial.customers_in_scope")


class ListCustomersInScopeUseCase:
    def __init__(
        self,
        *,
        repository: SellerPortfolioRepositoryPort,
        open_orders_metrics: OpenOrdersMetricsPort,
        list_service: ListCustomersInScopeService | None = None,
    ) -> None:
        self._repository = repository
        self._metrics = open_orders_metrics
        self._list_service = list_service or ListCustomersInScopeService()

    def execute(self, scope: CommercialCustomerScope) -> dict[str, Any]:
        assignments = self._resolve_assignments(scope)
        if not assignments:
            result = self._list_service.build(
                (),
                (),
                empty_portfolio=bool(scope.empty_portfolio),
                message=scope.message,
                metrics_available=True,
            )
            return self._to_payload(result)

        keys = [
            customer_coverage_key(item.customer_code, item.customer_store)
            for item in assignments
        ]
        metrics_available = True
        metrics_reason: str | None = None
        metrics: list = []
        try:
            metrics = self._metrics.list_customer_metrics(keys)
        except Exception:
            logger.exception("customers_in_scope_metrics_failed")
            metrics_available = False
            metrics_reason = "open_orders_metrics_fetch_failed"
            metrics = []

        result = self._list_service.build(
            assignments,
            metrics,
            empty_portfolio=False,
            message=None,
            metrics_available=metrics_available,
            metrics_reason=metrics_reason,
        )
        return self._to_payload(result)

    def _resolve_assignments(
        self, scope: CommercialCustomerScope
    ) -> list[SellerCustomerAssignment]:
        if scope.allowed_customers is not None:
            if not scope.allowed_customers:
                return []
            # Sempre union das carteiras ativas filtrada pelo allowlist
            # (portfolio_id no scope pode ser só a 1ª carteira do usuário).
            portfolios = self._repository.list_portfolios(active_only=True)
            return self._dedupe_assignments(
                [
                    assignment
                    for portfolio in portfolios
                    for assignment in portfolio.customers
                    if customer_coverage_key(
                        assignment.customer_code, assignment.customer_store
                    )
                    in scope.allowed_customers
                ]
            )

        # Irrestrito (team/manage) sem filtro de carteira: união de todas as carteiras.
        portfolios = self._repository.list_portfolios(active_only=True)
        return self._dedupe_assignments(
            [assignment for portfolio in portfolios for assignment in portfolio.customers]
        )

    @staticmethod
    def _dedupe_assignments(
        assignments: list[SellerCustomerAssignment],
    ) -> list[SellerCustomerAssignment]:
        seen: set[tuple[str, str]] = set()
        out: list[SellerCustomerAssignment] = []
        for assignment in assignments:
            key = customer_coverage_key(assignment.customer_code, assignment.customer_store)
            if not key[0] or not key[1] or key in seen:
                continue
            seen.add(key)
            out.append(
                SellerCustomerAssignment(
                    customer_code=key[0],
                    customer_store=key[1],
                    customer_name=assignment.customer_name,
                )
            )
        return out

    @staticmethod
    def _to_payload(result: CustomersInScopeResult) -> dict[str, Any]:
        return {
            "items": [
                {
                    "customer_code": item.customer_code,
                    "customer_store": item.customer_store,
                    "customer_name": item.customer_name,
                    "open_value": item.open_value,
                    "has_overdue": item.has_overdue,
                    "has_open_orders": item.has_open_orders,
                }
                for item in result.items
            ],
            "summary": {
                "customer_count": result.customer_count,
                "open_value_total": result.open_value_total,
                "overdue_customer_count": result.overdue_customer_count,
            },
            "empty_portfolio": result.empty_portfolio,
            "message": result.message,
            "metrics": {
                "available": result.metrics_available,
                "reason": result.metrics_reason,
            },
        }
