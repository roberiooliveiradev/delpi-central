from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.services.supplies.stock_value_estimation_payload_service import (
    build_stock_estimation_payload,
)
from app.application.services.supplies.stock_value_method_service import (
    STOCK_METHOD_RESOLVED_OFFICIAL,
)


def test_build_stock_estimation_payload_estimated_with_warning() -> None:
    request = GetStockValueRequest(
        start_date="2026-05-01",
        end_date="2026-05-31",
        stock_method="auto",
    )
    payload = build_stock_estimation_payload(
        request=request,
        bundle={
            "stock_method_resolved": "estimated",
            "estimation_meta": {
                "closing_base_date": "20260228",
                "closing_base_value": 100.0,
                "bridge_value": -20.0,
                "period_net_value": -10.0,
                "official_closure_on_period_end": False,
            },
        },
        period_start="20260501",
        period_end="20260531",
        period_end_exclusive="20260601",
    )

    assert payload["method"] == "sb9_last_closure_plus_sd3_movements"
    assert payload["stock_method_resolved"] == "estimated"
    assert payload["data_quality_warning"]


def test_build_stock_estimation_payload_official_closure() -> None:
    request = GetStockValueRequest(
        start_date="2026-05-01",
        end_date="2026-05-31",
        stock_method="auto",
    )
    payload = build_stock_estimation_payload(
        request=request,
        bundle={
            "stock_method_resolved": STOCK_METHOD_RESOLVED_OFFICIAL,
            "estimation_meta": {
                "official_closure_available": True,
                "official_closure_date": "20260531",
                "official_closure_value": 3_500_000.0,
                "official_closure_on_period_end": True,
            },
        },
        period_start="20260501",
        period_end="20260531",
        period_end_exclusive="20260601",
    )

    assert payload["method"] == "sb9_closure_on_end_date"
    assert "data_quality_warning" not in payload
