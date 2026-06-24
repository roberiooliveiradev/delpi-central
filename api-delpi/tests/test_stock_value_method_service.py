import pytest

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.services.supplies.stock_value_method_service import (
    resolve_stock_method_plan,
)


def test_auto_uses_official_when_closure_on_period_end() -> None:
    request = GetStockValueRequest(
        branch="01",
        start_date="2026-05-01",
        end_date="2026-05-31",
        stock_method="auto",
    )
    plan = resolve_stock_method_plan(
        request,
        [
            {
                "branch": "01",
                "official_closure_on_period_end": True,
            }
        ],
        period_end="20260531",
    )
    assert plan["resolved"] == "official_closure"
    assert plan["official_branches"] == ("01",)


def test_auto_uses_estimated_when_no_closure_on_period_end() -> None:
    request = GetStockValueRequest(
        branch="01",
        start_date="2026-05-01",
        end_date="2026-05-31",
        stock_method="auto",
    )
    plan = resolve_stock_method_plan(
        request,
        [
            {
                "branch": "01",
                "official_closure_on_period_end": False,
            }
        ],
        period_end="20260531",
    )
    assert plan["resolved"] == "estimated"
    assert plan["estimated_branches"] == ("01",)


def test_official_closure_requires_period_end_closure() -> None:
    request = GetStockValueRequest(
        branch="01",
        start_date="2026-05-01",
        end_date="2026-05-31",
        stock_method="official_closure",
    )
    with pytest.raises(ValueError, match="não há fechamento SB9010"):
        resolve_stock_method_plan(
            request,
            [{"branch": "01", "official_closure_on_period_end": False}],
            period_end="20260531",
        )


def test_estimated_forces_estimated_even_with_closure() -> None:
    request = GetStockValueRequest(
        branch="01",
        start_date="2026-05-01",
        end_date="2026-05-31",
        stock_method="estimated",
    )
    plan = resolve_stock_method_plan(
        request,
        [{"branch": "01", "official_closure_on_period_end": True}],
        period_end="20260531",
    )
    assert plan["resolved"] == "estimated"
