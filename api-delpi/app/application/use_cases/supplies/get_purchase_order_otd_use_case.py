from app.application.dto.supplies.purchase_order_otd_request import PurchaseOrderOtdRequest
from app.application.services.supplies.purchase_order_otd_cache import (
    get_cached_purchase_order_otd,
    purchase_order_otd_cache_key,
    set_cached_purchase_order_otd,
)
from app.domain.ports.supplies.purchase_order_otd_repository_port import (
    PurchaseOrderOtdRepositoryPort,
)
from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_RAW_MATERIAL


class GetPurchaseOrderOtdUseCase:
    def __init__(self, *, purchase_order_otd_repository: PurchaseOrderOtdRepositoryPort):
        self._repository = purchase_order_otd_repository

    def execute(self, request: PurchaseOrderOtdRequest) -> dict:
        cache_key = purchase_order_otd_cache_key(request)
        cached = get_cached_purchase_order_otd(cache_key)
        if cached is not None:
            return cached

        indicator = self._repository.get_purchase_order_otd(request)
        result = {
            "branch": indicator.branch,
            "start_date": indicator.start_date,
            "end_date": indicator.end_date,
            "product_type": PRODUCT_TYPE_RAW_MATERIAL,
            "total_lines": indicator.total_lines,
            "on_time_lines": indicator.on_time_lines,
            "late_lines": indicator.late_lines,
            "purchase_order_otd_pct": indicator.purchase_order_otd_pct,
        }
        set_cached_purchase_order_otd(cache_key, result)
        return result
