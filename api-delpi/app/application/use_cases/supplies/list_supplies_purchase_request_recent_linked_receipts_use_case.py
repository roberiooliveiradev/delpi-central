from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_linked_receipts_repository import (
    PurchaseRequestLinkedReceiptsRepository,
)


class ListSuppliesPurchaseRequestRecentLinkedReceiptsUseCase:
    def __init__(
        self,
        repository: PurchaseRequestLinkedReceiptsRepository | None = None,
    ) -> None:
        self._repository = repository or PurchaseRequestLinkedReceiptsRepository()

    def execute(
        self,
        *,
        after_recno: int | None = 0,
        limit: int | None = None,
    ) -> dict:
        return self._repository.list_recent_linked_receipts(
            after_recno=after_recno,
            limit=limit,
        )
