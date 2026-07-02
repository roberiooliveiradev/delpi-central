from __future__ import annotations

from app.domain.ports.production.production_orders_repository_port import (
    ProductionOrdersRepositoryPort,
)

_MIN_TERM_LENGTH = 3
_MAX_LIMIT = 20


class SearchProductionOrdersByOpUseCase:
    def __init__(self, production_orders_repository: ProductionOrdersRepositoryPort):
        self._production_orders_repository = production_orders_repository

    def execute(
        self,
        *,
        term: str,
        branches: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict]:
        normalized = (term or "").strip()
        if len(normalized) < _MIN_TERM_LENGTH:
            return []

        safe_limit = max(1, min(int(limit or 8), _MAX_LIMIT))
        clean_branches = [b for b in (branches or []) if b] or None

        return self._production_orders_repository.search_orders_by_op_prefix(
            term=normalized,
            branches=clean_branches,
            limit=safe_limit,
        )
