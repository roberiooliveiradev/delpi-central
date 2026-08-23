"""Dump TOTVS de SC1 em aberto com cobertura saldo + SC7 − SD4 + ESTSEG."""

from __future__ import annotations

from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.domain.services.supplies.purchase_request_open_coverage_service import (
    build_purchase_request_open_coverage,
)
from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES, normalize_branch_scope


class GetPurchaseRequestsOpenCoverageUseCase:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, *, branch: str) -> dict:
        scope = normalize_branch_scope(branch)
        if scope not in PROTHEUS_BRANCH_CODES:
            raise ValueError("branch deve ser 01 ou 02.")

        requests = self._repository.fetch_open_purchase_requests_for_branch(branch=scope)
        stocks = self._repository.fetch_available_stock_for_open_purchase_request_products(
            branch=scope
        )
        if not requests and not stocks:
            return {"items": [], "products": []}

        orders = self._repository.fetch_open_purchase_orders_for_branch(branch=scope)
        commitments = self._repository.fetch_open_commitments_for_branch(branch=scope)
        return build_purchase_request_open_coverage(
            requests=requests,
            stocks=stocks,
            orders=orders,
            commitments=commitments,
        )
