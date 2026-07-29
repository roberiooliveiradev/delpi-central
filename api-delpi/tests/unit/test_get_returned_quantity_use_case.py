from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.ppm.returned_quantity_query_request import (
    ReturnedQuantityQueryRequest,
)
from app.application.use_cases.ppm.get_returned_quantity_use_case import (
    GetReturnedQuantityUseCase,
)


def test_returned_quantity_query_request_validates_type() -> None:
    try:
        ReturnedQuantityQueryRequest.create(
            ppm_type="all",
            date_start="2026-01-01",
            date_end="2026-01-31",
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "internal ou external" in str(exc)


def test_get_returned_quantity_use_case_get_totals() -> None:
    repository = MagicMock()
    repository.get_returned_totals.return_value = {
        "qty_returned_un": 12.5,
        "nc_count": 3,
    }
    use_case = GetReturnedQuantityUseCase(repository)
    request = ReturnedQuantityQueryRequest.create(
        ppm_type="external",
        date_start="2026-01-01",
        date_end="2026-01-31",
        branch="01",
        product_prefix="9026",
    )

    result = use_case.get_totals(request)

    assert result["qty_returned_un"] == 12.5
    assert result["nc_count"] == 3
    assert result["type"] == "external"
    assert result["product_prefix"] == "9026"
    repository.get_returned_totals.assert_called_once_with(
        ppm_type="external",
        branch="01",
        date_start="2026-01-01",
        date_end="2026-01-31",
        product_prefix="9026",
    )
