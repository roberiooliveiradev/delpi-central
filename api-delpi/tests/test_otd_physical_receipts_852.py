"""GLPI #852 — paridade fiscal, virada de período e falha fechada."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.application.dto.supplies.get_purchase_order_otd_panel_request import (
    GetPurchaseOrderOtdPanelRequest,
)
from app.application.dto.supplies.purchase_order_otd_request import PurchaseOrderOtdRequest
from app.infrastructure.persistence.totvs.supplies_repositories import (
    otd_physical_receipts as physical,
)
from app.infrastructure.persistence.totvs.supplies_repositories.otd_query_repository import (
    OtdQueryRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_order_otd_repository import (
    PurchaseOrderOtdRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_order_otd_sql import (
    build_purchase_order_otd_lines_list_sql,
)


ROW = {
    "branch_code": "01",
    "supplier_code": "000123",
    "supplier_store": "01",
    "document_match_key": "000001234",
    "series": "001",
    "sf1_recno": 123456,
    "received_date": "2026-08-31",
    "erp_entry_date": "2026-09-02",
}


def test_lnf_series_is_canonical_and_malformed_keys_fail_closed():
    result = physical._validate_rows({"complete": True, "items": [ROW]}, branch="01")
    assert result[0]["series"] == "1"
    assert result[0]["received_date"] == "2026-08-31"
    with pytest.raises(physical.PhysicalOtdSourceUnavailable):
        physical._validate_rows({"complete": False, "items": []}, branch="01")
    with pytest.raises(physical.PhysicalOtdSourceUnavailable):
        physical._validate_rows({"complete": True, "items": [ROW, ROW]}, branch="01")
    with pytest.raises(physical.PhysicalOtdSourceUnavailable):
        physical._validate_rows(
            {"complete": True, "items": [{**ROW, "branch_code": "02"}]}, branch="01"
        )


def test_physical_sql_matches_exact_fiscal_identity_no_fanout_and_filters_effective_time():
    source = physical.build_physical_source(
        physical._validate_rows({"complete": True, "items": [ROW]}, branch="01"),
        start_date="2026-08-01",
        end_date="2026-08-31",
    )
    assert "OPENJSON(CAST(? AS NVARCHAR(MAX)))" in source.cte
    assert "LNF.supplier_code = RTRIM(D1.D1_FORNECE)" in source.cte
    assert "LNF.supplier_store = RTRIM(D1.D1_LOJA)" in source.cte
    assert "LNF.document_match_key = RIGHT('000000000' + RTRIM(D1.D1_DOC), 9)" in source.cte
    assert "LNF.series =" in source.cte
    assert "D1.D1_PEDIDO = SC7.C7_NUM" in source.cte
    assert "D1.D1_ITEMPC = SC7.C7_ITEM" in source.cte
    assert "DT_DIGITACAO_ERP" in source.cte
    assert "OR LNF.received_date IS NOT NULL" in source.cte  # 31/08 fisico; 02/09 ERP
    assert "COALESCE(LNF.received_date, CONVERT(date, D1.D1_DTDIGIT, 112))" in source.cte
    assert "DATEDIFF(" in source.cte
    assert "RECEIPT_SOURCE" in source.cte
    assert source.params[1:] == ("20260801", "20260831")
    assert '"series":"1"' in source.params[0]


def test_feature_gate_never_calls_remote_when_off(monkeypatch):
    monkeypatch.delenv("OTD_PHYSICAL_RECEIPTS_ENABLED", raising=False)
    monkeypatch.setattr(physical.requests, "get", lambda *a, **k: 1 / 0)
    assert physical.resolve_physical_source(
        SimpleNamespace(), branch="01", start_date="2026-08-01", end_date="2026-08-31"
    ) is None


def test_unbounded_period_uses_lnf_start_and_today_not_unbounded_year_9999(monkeypatch):
    monkeypatch.setenv("OTD_PHYSICAL_RECEIPTS_ENABLED", "true")
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "test")
    seen = {}
    class Response:
        def raise_for_status(self):
            return None
        def json(self):
            return {"complete": True, "items": []}
    def remote(_url, **kwargs):
        seen.update(kwargs["params"])
        return Response()
    monkeypatch.setattr(physical.requests, "get", remote)
    physical.resolve_physical_source(
        SimpleNamespace(), branch="01", start_date=None, end_date=None
    )
    assert seen["start_date"] == "2026-01-01"
    assert seen["end_date"] == physical.date.today().isoformat()


def test_legacy_period_before_lnf_bypasses_unnecessary_remote_read(monkeypatch):
    monkeypatch.setenv("OTD_PHYSICAL_RECEIPTS_ENABLED", "true")
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "test")
    monkeypatch.setattr(
        physical.requests, "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("not called"))
    )
    source = physical.resolve_physical_source(
        SimpleNamespace(), branch="01",
        start_date="2025-01-01", end_date="2025-12-31",
    )
    assert source is not None and source.params[0] == "[]"


def test_enabled_feed_failure_does_not_silently_use_erp_date(monkeypatch):
    monkeypatch.setenv("OTD_PHYSICAL_RECEIPTS_ENABLED", "true")
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "test")
    def remote(*args, **kwargs):
        raise physical.requests.Timeout("indisponivel")
    monkeypatch.setattr(physical.requests, "get", remote)
    with pytest.raises(physical.PhysicalOtdSourceUnavailable):
        physical.resolve_physical_source(
            SimpleNamespace(), branch="01", start_date="2026-08-01", end_date="2026-08-31"
        )


def test_enabled_feed_requests_both_dates_and_memoizes_per_request(monkeypatch):
    monkeypatch.setenv("OTD_PHYSICAL_RECEIPTS_ENABLED", "true")
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "test")
    called = []
    class Response:
        def raise_for_status(self):
            return None
        def json(self):
            return {"complete": True, "items": [ROW]}
    def remote(url, **kwargs):
        called.append((url, kwargs))
        return Response()
    monkeypatch.setattr(physical.requests, "get", remote)
    repo = SimpleNamespace()
    first = physical.resolve_physical_source(
        repo, branch="01", start_date="2026-08-01", end_date="2026-08-31"
    )
    second = physical.resolve_physical_source(
        repo, branch="01", start_date="2026-08-01", end_date="2026-08-31"
    )
    assert first is second
    assert len(called) == 1
    assert called[0][1]["params"]["start_date"] == "2026-08-01"
    assert called[0][1]["params"]["end_date"] == "2026-08-31"


def test_legacy_list_stays_unchanged_without_feature(monkeypatch):
    monkeypatch.setenv("OTD_PHYSICAL_RECEIPTS_ENABLED", "false")
    repo = OtdQueryRepository()
    monkeypatch.setattr(repo, "__enter__", lambda: repo)
    prefix, table, bind, enabled = repo._source(GetOTDRequest(branch="01"))
    assert (prefix, table, bind, enabled) == (
        "", "VW_PONTUALIDADE_FORNECEDORES WITH (NOLOCK)", (), False
    )


def test_purchase_order_physical_kpi_uses_same_source_and_filter(monkeypatch):
    synthetic = physical.build_physical_source([ROW], start_date="2026-08-01", end_date="2026-08-31")
    monkeypatch.setattr(
        "app.infrastructure.persistence.totvs.supplies_repositories.purchase_order_otd_repository.resolve_physical_source",
        lambda *a, **k: synthetic,
    )
    repo = PurchaseOrderOtdRepository()
    executed = []
    monkeypatch.setattr(repo, "__enter__", lambda: repo)
    monkeypatch.setattr(repo, "__exit__", lambda *a: None)
    # MagicMock attr on instance cannot override special methods: patch the class.
    monkeypatch.setattr(PurchaseOrderOtdRepository, "__enter__", lambda self: self)
    monkeypatch.setattr(PurchaseOrderOtdRepository, "__exit__", lambda self, *a: None)
    repo.execute_one = lambda sql, params: (
        executed.append((sql, params)) or {
            "total_lines": 1, "on_time_lines": 1, "late_lines": 0,
            "purchase_order_otd_pct": 100.0,
        }
    )
    result = repo.get_purchase_order_otd(
        PurchaseOrderOtdRequest(branch="01", start_date="2026-08-01", end_date="2026-08-31")
    )
    assert result.on_time_lines == 1
    assert "FROM OTD_EFFECTIVE" in executed[0][0]
    assert executed[0][1][:3] == synthetic.params
    assert "DT_DIGITACAO" in executed[0][0]


def test_panel_sql_exposes_erp_and_effective_receipt_date_separately():
    request = GetPurchaseOrderOtdPanelRequest(page=1, page_size=20)
    source = physical.build_physical_source([ROW], start_date="2026-08-01", end_date="2026-08-31")
    sql = build_purchase_order_otd_lines_list_sql(
        where_clause="DT_DIGITACAO BETWEEN ? AND ?",
        request=request, source_cte=source.cte, source_table="OTD_EFFECTIVE",
    )
    assert "V.DT_DIGITACAO_ERP" in sql
    assert "receipt_effective_date" in sql
    assert "receipt_source" in sql
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql
    assert "LNF_RECEIPTS AS" in sql


def test_general_otd_month_bucket_is_effective_date_not_digit_date(monkeypatch):
    source = physical.build_physical_source([ROW], start_date="2026-08-01", end_date="2026-08-31")
    monkeypatch.setattr(
        "app.infrastructure.persistence.totvs.supplies_repositories.otd_query_repository.resolve_physical_source",
        lambda *a, **k: source,
    )
    monkeypatch.setattr(OtdQueryRepository, "__enter__", lambda self: self)
    monkeypatch.setattr(OtdQueryRepository, "__exit__", lambda self, *a: None)
    repo = OtdQueryRepository()
    queries = []
    repo.execute_query = lambda sql, params: (queries.append((sql, params)) or [])
    repo.get_otd_monthly_breakdown(
        GetOTDRequest(branch="01", start_date="2026-08-01", end_date="2026-08-31")
    )
    sql, params = queries[0]
    assert "FROM OTD_EFFECTIVE" in sql
    assert "YEAR(DT_DIGITACAO)" in sql
    assert "MONTH(DT_DIGITACAO)" in sql
    assert params[:3] == source.params
