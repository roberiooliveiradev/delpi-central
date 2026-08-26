from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_repository import (
    PurchaseRequestLinesRepository,
)


class GetSuppliesPurchaseRequestLinesUseCase:
    def __init__(self, repository: PurchaseRequestLinesRepository | None = None) -> None:
        self._repository = repository or PurchaseRequestLinesRepository()

    def execute(
        self,
        *,
        branch: str,
        request_number: str,
        cost_centers: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        lines = self._repository.get_request_lines(
            branch=branch,
            request_number=request_number,
            cost_centers=cost_centers,
            date_from=date_from,
            date_to=date_to,
        )
        return {"lines": lines}
