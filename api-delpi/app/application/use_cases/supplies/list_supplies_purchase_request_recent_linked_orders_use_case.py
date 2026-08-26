from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_linked_orders_repository import (
    PurchaseRequestLinkedOrdersRepository,
)


class ListSuppliesPurchaseRequestRecentLinkedOrdersUseCase:
    def __init__(
        self,
        repository: PurchaseRequestLinkedOrdersRepository | None = None,
    ) -> None:
        self._repository = repository or PurchaseRequestLinkedOrdersRepository()

    def execute(
        self,
        *,
        after_recno: int | None = 0,
        limit: int | None = None,
    ) -> dict:
        return self._repository.list_recent_linked_orders(
            after_recno=after_recno,
            limit=limit,
        )
