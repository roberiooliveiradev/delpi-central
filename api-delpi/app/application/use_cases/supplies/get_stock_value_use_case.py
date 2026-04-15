from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.domain.ports.supplies.stock_value_query_repository_port import (
    StockValueQueryRepositoryPort,
)


class GetStockValueUseCase:

    def __init__(self, repository: StockValueQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetStockValueRequest) -> dict:
        summary = self._repository.get_stock_value_summary(request)
        by_branch = self._repository.get_stock_value_by_branch(request)
        by_location = self._repository.get_stock_value_by_location(request)
        top_products = self._repository.get_top_products_by_stock_value(request)

        total_stock_value = float(summary.get("total_stock_value") or 0)
        total_stock_quantity = float(summary.get("total_stock_quantity") or 0)

        average_unit_value = (
            total_stock_value / total_stock_quantity
            if total_stock_quantity > 0 else 0
        )

        return {
            "branch": summary.get("branch") or request.branch or "consolidated",
            "location": summary.get("location") or request.location or "all",
            "summary": {
                "total_stock_value": total_stock_value,
                "total_stock_quantity": total_stock_quantity,
                "total_records": int(summary.get("total_records") or 0),
                "total_products": int(summary.get("total_products") or 0),
                "total_locations": int(summary.get("total_locations") or 0),
                "average_unit_value": average_unit_value,
            },
            "by_branch": by_branch,
            "by_location": by_location,
            "top_products": top_products,
        }