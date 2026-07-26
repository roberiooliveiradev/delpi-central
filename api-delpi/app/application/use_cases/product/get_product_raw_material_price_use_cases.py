from app.application.dto.product.product_raw_material_price_request import (
    ProductRawMaterialPriceRequest,
)
from app.application.services.product.product_raw_material_price_service import (
    build_raw_material_price_intelligence,
    enrich_price_history_with_variation,
    resolve_history_date_range,
    summarize_budget_history,
    summarize_price_history,
)
from app.domain.ports.product.product_raw_material_price_repository_port import (
    ProductRawMaterialPriceRepositoryPort,
)


class _ProductRawMaterialPriceBaseUseCase:

    DEFAULT_HISTORY_LIMIT = 24

    def __init__(self, repository: ProductRawMaterialPriceRepositoryPort):
        self._repository = repository

    def _resolve_limit(self, request: ProductRawMaterialPriceRequest) -> int:
        limit = request.history_limit or self.DEFAULT_HISTORY_LIMIT
        return max(1, min(limit, 200))

    def _resolve_dates(
        self, request: ProductRawMaterialPriceRequest
    ) -> tuple[str, str]:
        return resolve_history_date_range(request.date_start, request.date_end)


class GetProductLastPurchaseUseCase(_ProductRawMaterialPriceBaseUseCase):

    def execute(self, request: ProductRawMaterialPriceRequest) -> dict:
        header = self._repository.fetch_product_header(request.code)
        if not header:
            return {"product": None, "last_purchase": None}

        last_purchase = self._repository.fetch_last_purchase(
            request.code,
            branch=request.branch,
        )
        return {
            "product": header,
            "last_purchase": last_purchase,
        }


class GetProductPurchasePriceHistoryUseCase(_ProductRawMaterialPriceBaseUseCase):

    def execute(self, request: ProductRawMaterialPriceRequest) -> dict:
        header = self._repository.fetch_product_header(request.code)
        if not header:
            return {"product": None, "items": [], "summary": summarize_price_history([])}

        date_start, date_end_exclusive = self._resolve_dates(request)
        raw_items = self._repository.fetch_purchase_price_history(
            request.code,
            date_start,
            date_end_exclusive,
            branch=request.branch,
            limit=self._resolve_limit(request),
        )
        items = enrich_price_history_with_variation(raw_items)

        return {
            "product": header,
            "start_date": date_start,
            "date_end_exclusive": date_end_exclusive,
            "branch": request.branch,
            "items": items,
            "summary": summarize_price_history(items),
        }


class GetProductPurchaseBudgetHistoryUseCase(_ProductRawMaterialPriceBaseUseCase):

    def execute(self, request: ProductRawMaterialPriceRequest) -> dict:
        header = self._repository.fetch_product_header(request.code)
        if not header:
            return {"product": None, "items": [], "summary": summarize_budget_history([])}

        date_start, date_end_exclusive = self._resolve_dates(request)
        items = self._repository.fetch_purchase_budget_history(
            request.code,
            date_start,
            date_end_exclusive,
            branch=request.branch,
        )

        return {
            "product": header,
            "start_date": date_start,
            "date_end_exclusive": date_end_exclusive,
            "branch": request.branch,
            "items": items,
            "summary": summarize_budget_history(items),
        }


class GetProductRawMaterialPriceIntelligenceUseCase(_ProductRawMaterialPriceBaseUseCase):

    def execute(self, request: ProductRawMaterialPriceRequest) -> dict:
        header = self._repository.fetch_product_header(request.code)
        if not header:
            return build_raw_material_price_intelligence(
                product=None,
                last_purchase=None,
                price_history_raw=[],
                budget_history_raw=[],
                date_start="",
                date_end_exclusive="",
                branch=request.branch,
            )

        date_start, date_end_exclusive = self._resolve_dates(request)
        limit = self._resolve_limit(request)

        last_purchase = self._repository.fetch_last_purchase(
            request.code,
            branch=request.branch,
        )
        price_history_raw = self._repository.fetch_purchase_price_history(
            request.code,
            date_start,
            date_end_exclusive,
            branch=request.branch,
            limit=limit,
        )
        budget_history_raw = self._repository.fetch_purchase_budget_history(
            request.code,
            date_start,
            date_end_exclusive,
            branch=request.branch,
        )

        return build_raw_material_price_intelligence(
            product=header,
            last_purchase=last_purchase,
            price_history_raw=price_history_raw,
            budget_history_raw=budget_history_raw,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.branch,
        )
