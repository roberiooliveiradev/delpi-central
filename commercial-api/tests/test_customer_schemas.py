from __future__ import annotations

import pytest
from pydantic import ValidationError

from commercial_app.interface.http.schemas.portfolio_schemas import (
    CustomerCoverageLookupBody,
    EnrichmentBody,
)


def _customers(count: int) -> list[dict[str, str]]:
    return [
        {
            "customer_code": str(index + 1).zfill(6),
            "customer_store": "01",
        }
        for index in range(count)
    ]


def test_enrichment_body_accepts_up_to_200_customers() -> None:
    body = EnrichmentBody.model_validate({"customers": _customers(200)})

    assert len(body.customers) == 200


def test_enrichment_body_rejects_201_customers() -> None:
    with pytest.raises(ValidationError):
        EnrichmentBody.model_validate({"customers": _customers(201)})


def test_customer_coverage_lookup_body_accepts_customers_and_portfolio_ids() -> None:
    body = CustomerCoverageLookupBody.model_validate(
        {
            "customers": _customers(2),
            "portfolio_ids": ["p1", "p2"],
        }
    )
    assert len(body.customers) == 2
    assert body.portfolio_ids == ["p1", "p2"]


def test_customer_coverage_lookup_body_rejects_201_customers() -> None:
    with pytest.raises(ValidationError):
        CustomerCoverageLookupBody.model_validate({"customers": _customers(201)})
