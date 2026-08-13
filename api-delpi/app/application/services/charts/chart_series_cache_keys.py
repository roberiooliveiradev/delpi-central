from __future__ import annotations

from app.application.dto.commercial.commercial_rol_series_request import (
    CommercialRolSeriesRequest,
)
from app.application.dto.commercial.sales_conversion_rate_series_request import (
    SalesConversionRateSeriesRequest,
)
from app.application.dto.commercial.sales_conversion_rate_series_request import (
    SalesConversionRateSeriesRequest,
)
from app.application.dto.commercial.sales_order_otd_series_request import (
    SalesOrderOtdSeriesRequest,
)
from app.application.dto.production.production_oee_series_request import (
    ProductionOeeSeriesRequest,
)
from app.application.dto.production.production_otd_series_request import (
    ProductionOtdSeriesRequest,
)
from app.application.dto.ppm.ppm_series_request import PpmSeriesRequest
from app.application.dto.supplies.purchase_order_otd_series_request import (
    PurchaseOrderOtdSeriesRequest,
)

def commercial_rol_series_cache_key(request: CommercialRolSeriesRequest) -> str:
    return "|".join(
        [
            "commercial-rol-series",
            request.granularity,
            request.date_start or "",
            request.date_end or "",
            request.customer_segment or "",
            ",".join(request.customer_codes or []),
        ]
    )


def production_oee_series_cache_key(request: ProductionOeeSeriesRequest) -> str:
    return "|".join(
        [
            "production-oee-series",
            request.granularity,
            request.date_start or "",
            request.date_end or "",
            request.branch or "",
        ]
    )


def commercial_sales_conversion_rate_series_cache_key(
    request: SalesConversionRateSeriesRequest,
) -> str:
    return "|".join(
        [
            "commercial-closing-rate-series",
            request.granularity,
            request.date_start or "",
            request.date_end or "",
            request.customer_segment or "",
            ",".join(request.customer_codes or []),
        ]
    )


def commercial_sales_order_otd_series_cache_key(
    request: SalesOrderOtdSeriesRequest,
) -> str:
    return "|".join(
        [
            "commercial-sales-order-otd-series",
            request.granularity,
            request.date_start or "",
            request.date_end or "",
            request.branch or "",
            request.customer_segment or "",
            ",".join(getattr(request, "customer_codes", None) or []),
        ]
    )


def supplies_purchase_order_otd_series_cache_key(
    request: PurchaseOrderOtdSeriesRequest,
) -> str:
    return "|".join(
        [
            "supplies-purchase-order-otd-series",
            request.granularity,
            request.date_start or "",
            request.date_end or "",
            request.branch or "",
        ]
    )


def production_otd_series_cache_key(request: ProductionOtdSeriesRequest) -> str:
    return "|".join(
        [
            "production-otd-series",
            request.granularity,
            request.date_start or "",
            request.date_end or "",
            request.branch or "",
        ]
    )


def ppm_series_cache_key(request: PpmSeriesRequest) -> str:
    return "|".join(
        [
            f"ppm-{request.type}-series",
            request.granularity,
            request.date_start or "",
            request.date_end or "",
            request.branch or "",
            request.product_prefix or "",
        ]
    )
