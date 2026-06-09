import pytest

from app.application.dto.ppm.produced_quantity_request import ProducedQuantityRequest


def test_produced_quantity_request_normalizes_products() -> None:
    dto = ProducedQuantityRequest(
        products=["50232465", "50233615,50233616", "50232465"],
        date_start="2026-01-01",
        date_end="2026-01-31",
        branch="01",
    )

    assert dto.products == ["50232465", "50233615", "50233616"]
    assert dto.branch == "01"


def test_produced_quantity_request_requires_products() -> None:
    with pytest.raises(ValueError, match="ao menos um código"):
        ProducedQuantityRequest(
            products=[],
            date_start="2026-01-01",
            date_end="2026-01-31",
        )


def test_produced_quantity_request_requires_dates() -> None:
    with pytest.raises(ValueError, match="date_start"):
        ProducedQuantityRequest(
            products=["50232465"],
            date_start="",
            date_end="2026-01-31",
        )

    with pytest.raises(ValueError, match="date_end"):
        ProducedQuantityRequest(
            products=["50232465"],
            date_start="2026-01-01",
            date_end="",
        )
