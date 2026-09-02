from __future__ import annotations

from typing import Any

from financial_app.infrastructure.gateways.delpi_financial_gateway import (
    DelpiFinancialGateway,
)


class RecordingGateway(DelpiFinancialGateway):
    """Captura o que iria para a api-delpi em vez de abrir conexão HTTP."""

    def __init__(self) -> None:
        super().__init__(base_url="http://delpi-api-delpi:8000")
        self.method: str | None = None
        self.path: str | None = None
        self.params: dict[str, Any] = {}

    def _request(self, method, path, *, params=None, json_body=None):
        self.method = method
        self.path = path
        self.params = dict(params or {})
        return {"success": True, "message": "OK", "data": {"items": []}}


def _call(**overrides: Any) -> RecordingGateway:
    gateway = RecordingGateway()
    kwargs: dict[str, Any] = {
        "branch": "01",
        "issue_start": "2026-03-01",
        "issue_end": "2026-03-31",
        "entry_start": None,
        "entry_end": None,
        "supplier": None,
        "invoice_document": None,
        "freight_document": None,
        "limit": 20000,
    }
    kwargs.update(overrides)
    gateway.fetch_purchase_freight_links(**kwargs)
    return gateway


def test_reads_the_canonical_api_delpi_path() -> None:
    gateway = _call()

    assert gateway.method == "GET"
    assert gateway.path == "/financial/purchase-freight/links"


def test_forwards_every_filter_in_snake_case() -> None:
    gateway = _call(
        entry_start="2026-02-01",
        entry_end="2026-02-28",
        supplier="001992",
        invoice_document="000123456",
        freight_document="000000789",
    )

    assert gateway.params == {
        "branch": "01",
        "issue_start": "2026-03-01",
        "issue_end": "2026-03-31",
        "entry_start": "2026-02-01",
        "entry_end": "2026-02-28",
        "supplier": "001992",
        "invoice_document": "000123456",
        "freight_document": "000000789",
        "limit": 20000,
    }


def test_consolidated_branch_is_forwarded_as_none() -> None:
    gateway = _call(branch=None)

    assert gateway.params["branch"] is None


def test_gateway_holds_no_business_rule() -> None:
    """Rateio, limite e situação são do domínio — o gateway só transporta."""
    import inspect

    source = inspect.getsource(
        DelpiFinancialGateway.fetch_purchase_freight_links  # type: ignore[attr-defined]
    )

    for forbidden in ("Decimal", "limit_percent", "allocat", "situation", "SELECT"):
        assert forbidden not in source
