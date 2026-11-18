"""#852 — contrato de segurança e integridade do snapshot interno LNF."""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from controllership_finance_app.interface.http.routes.invoice_posting import otd_receipts_routes as route


def _request():
    return SimpleNamespace(headers={"X-Delpi-Service-Token": "test"})


def test_internal_feed_rejects_missing_or_invalid_service_identity(monkeypatch):
    monkeypatch.setattr(route, "request_has_valid_internal_service_token", lambda _req: False)
    with pytest.raises(HTTPException) as exc:
        route.get_internal_lnf_otd_receipts(
            _request(), start_date=date(2026, 8, 1), end_date=date(2026, 8, 31), branch="01"
        )
    assert exc.value.status_code == 403


def test_feed_exposes_only_matched_invoice_identity_and_local_receipt_date(monkeypatch):
    monkeypatch.setattr(route, "request_has_valid_internal_service_token", lambda _req: True)
    seen = {}
    class Repository:
        def fetch_all(self, sql, params):
            seen["sql"], seen["params"] = sql, params
            return [{
                "branch_code": "01", "document_match_key": "000001234",
                "supplier_code": "000012", "supplier_store": "01",
                "series": "1", "sf1_recno": 155,
                "received_date": date(2026, 8, 12), "erp_entry_date": date(2026, 8, 14),
            }]
    monkeypatch.setattr(route, "PostgresInvoicePostingRepository", Repository)
    value = route.get_internal_lnf_otd_receipts(
        _request(), start_date=date(2026, 8, 1), end_date=date(2026, 8, 31), branch="01"
    )
    assert value["complete"] is True
    assert len(value["items"]) == 1
    assert value["items"][0]["received_date"] == "2026-08-12"
    assert value["items"][0]["erp_entry_date"] == "2026-08-14"
    assert "supplier_name" not in value["items"][0]
    assert "status = 'posted'" in seen["sql"]
    assert "sf1_recno IS NOT NULL" in seen["sql"]
    assert "fiscal_key_count = 1" in seen["sql"]
    assert seen["params"][:2] == ("01", "01")


def test_feed_does_not_publish_a_truncated_or_invalid_range(monkeypatch):
    monkeypatch.setattr(route, "request_has_valid_internal_service_token", lambda _req: True)
    with pytest.raises(HTTPException) as invalid:
        route.get_internal_lnf_otd_receipts(
            _request(), start_date=date(2026, 9, 1), end_date=date(2026, 8, 31), branch="01"
        )
    assert invalid.value.status_code == 422
    class Repository:
        def fetch_all(self, _sql, _params):
            return [{}] * (route._MAX_ROWS + 1)
    monkeypatch.setattr(route, "PostgresInvoicePostingRepository", Repository)
    with pytest.raises(HTTPException) as overflow:
        route.get_internal_lnf_otd_receipts(
            _request(), start_date=date(2026, 8, 1), end_date=date(2026, 8, 31), branch="01"
        )
    assert overflow.value.status_code == 503
