"""R2 read use cases — Comex imports and IPP observations (PROC-0076)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.application import market_data_queries as mdq
from app.application.contracts import (
    ContractNotReadyError,
    InvalidQueryError,
    UnknownSeriesError,
    UseNotApprovedError,
)
from app.domain.market_data import MarketDataSource


class _FakeConnCtx:
    def __enter__(self):
        return object()

    def __exit__(self, *exc):
        return False


def _source(source_id, **over):
    base = dict(
        source_id=source_id,
        provider_id=source_id,
        source_kind="api",
        attribution="Fonte oficial",
        license_reference="open-data",
        license_reviewed_at=date(2026, 10, 27),
        allowed_use_scope="collect;store;derive;internal_display",
        active=True,
    )
    base.update(over)
    return MarketDataSource(**base)


def _ncm(**over):
    base = dict(
        ncm_code="12345678",
        ncm_version="NCM2022",
        description="Produto homologado",
        family_code="metals",
        active=True,
    )
    base.update(over)
    return base


def _series(**over):
    base = dict(
        series_id="ipp-metalurgia-index",
        table_code="6903",
        classification_code="842",
        variable_code="10008",
        variable_label="Número-índice",
        activity_code="46641",
        activity_label="24 METALURGIA",
        metric_kind="ipp_index",
        unit_code="index",
        unit_label="número-índice",
        base_reference="dez/2018=100",
        source_id="ibge-ipp-sidra",
        active=True,
    )
    base.update(over)
    return base


def _comex_row(**over):
    base = dict(
        observation_id=1,
        reference_month=date(2026, 8, 1),
        ncm_code="12345678",
        ncm_version="NCM2022",
        country_code="160",
        state_code="SC",
        fob_usd_total=Decimal("14000"),
        net_weight_kg_total=Decimal("4000"),
        unit_value_usd_per_t=Decimal("3500"),
        contributing_rows=2,
        quality_status="validated",
        dataset_year=2026,
        dataset_revision=None,
        source_checksum="abc",
        source_id="mdic-comex-stat",
        retrieved_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        revised_at=None,
    )
    base.update(over)
    return base


def _ipp_row(**over):
    base = dict(
        observation_id=1,
        series_id="ipp-metalurgia-index",
        reference_month=date(2026, 8, 1),
        value=Decimal("184.02"),
        quality_status="validated",
        source_id="ibge-ipp-sidra",
        source_record_key="sidra:10008:46641:202608",
        published_at=None,
        retrieved_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        revised_at=None,
    )
    base.update(over)
    return base


class FakeRepo:
    def __init__(self, **kw):
        self.kw = kw

    def get_source(self, source_id):
        sources = self.kw.get(
            "sources",
            {
                "mdic-comex-stat": _source("mdic-comex-stat"),
                "ibge-ipp-sidra": _source("ibge-ipp-sidra"),
            },
        )
        return sources.get(source_id)

    def get_ncm_allowlist(self, code):
        rows = {r["ncm_code"]: r for r in self.kw.get("ncms", [_ncm()])}
        return rows.get(code)

    def list_comex_observations(self, **kw):
        self.last_comex_query = kw
        return self.kw.get("comex_rows", [_comex_row()])

    def get_producer_price_series(self, series_id):
        rows = {s["series_id"]: s for s in self.kw.get("series", [_series()])}
        return rows.get(series_id)

    def list_producer_price_observations(self, **kw):
        self.last_ipp_query = kw
        return self.kw.get("ipp_rows", [_ipp_row()])


@pytest.fixture
def repo(monkeypatch):
    repo = FakeRepo()
    monkeypatch.setattr(mdq, "get_connection", lambda: _FakeConnCtx())
    monkeypatch.setattr(
        mdq, "MarketDataRepository", lambda conn, schema: repo
    )
    monkeypatch.setattr(mdq, "check_market_contract_ready", lambda conn: None)
    monkeypatch.setattr(
        mdq.Settings, "plugins_db_configured", classmethod(lambda cls: True)
    )
    return repo


def test_comex_imports_positive(repo):
    payload = mdq.list_comex_imports(
        ncm_code="12345678",
        date_from_raw="2026-01-01",
        date_to_raw="2026-12-31",
        country_code=None,
        state_code=None,
        limit_raw=None,
        cursor_raw=None,
    )
    assert payload["meta"]["data_status"] == "ok"
    item = payload["items"][0]
    assert item["unit_value_usd_per_t"] == "3500"
    assert item["unit"] == "USD/metric ton"
    assert item["dimensions"] == {"country_code": "160", "state_code": "SC"}
    assert repo.last_comex_query["ncm_code"] == "12345678"


def test_comex_unapproved_ncm_is_404(repo):
    with pytest.raises(UnknownSeriesError):
        mdq.list_comex_imports(
            ncm_code="99999999",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            country_code=None,
            state_code=None,
            limit_raw=None,
            cursor_raw=None,
        )


def test_comex_dimension_filters_propagate(repo):
    mdq.list_comex_imports(
        ncm_code="12345678",
        date_from_raw="2026-01-01",
        date_to_raw="2026-12-31",
        country_code="160",
        state_code="sc",
        limit_raw=None,
        cursor_raw=None,
    )
    assert repo.last_comex_query["country_code"] == "160"
    assert repo.last_comex_query["state_code"] == "sc"


def test_comex_display_pending_blocks(monkeypatch, repo):
    repo.kw["sources"] = {
        "mdic-comex-stat": _source(
            "mdic-comex-stat",
            allowed_use_scope="collect;store;internal_display_pending_review",
        )
    }
    with pytest.raises(UseNotApprovedError):
        mdq.list_comex_imports(
            ncm_code="12345678",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            country_code=None,
            state_code=None,
            limit_raw=None,
            cursor_raw=None,
        )


def test_comex_contract_not_ready_blocks(monkeypatch, repo):
    def _boom(conn):
        raise ContractNotReadyError("revision V004 not applied")

    monkeypatch.setattr(mdq, "check_market_contract_ready", _boom)
    with pytest.raises(ContractNotReadyError):
        mdq.list_comex_imports(
            ncm_code="12345678",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            country_code=None,
            state_code=None,
            limit_raw=None,
            cursor_raw=None,
        )


def test_comex_invalid_date_rejected(repo):
    with pytest.raises(InvalidQueryError):
        mdq.list_comex_imports(
            ncm_code="12345678",
            date_from_raw="bad",
            date_to_raw="2026-12-31",
            country_code=None,
            state_code=None,
            limit_raw=None,
            cursor_raw=None,
        )


def test_ipp_positive(repo):
    payload = mdq.list_producer_price_observations(
        series_id="ipp-metalurgia-index",
        date_from_raw="2026-01-01",
        date_to_raw="2026-12-31",
        limit_raw=None,
        cursor_raw=None,
    )
    assert payload["series"]["metric_kind"] == "ipp_index"
    assert payload["series"]["base_reference"] == "dez/2018=100"
    assert payload["items"][0]["value"] == "184.02"


def test_ipp_unknown_series_is_404(repo):
    with pytest.raises(UnknownSeriesError):
        mdq.list_producer_price_observations(
            series_id="ipp-inexistente",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            limit_raw=None,
            cursor_raw=None,
        )


def test_ipp_display_pending_blocks(repo):
    repo.kw["sources"] = {
        "ibge-ipp-sidra": _source(
            "ibge-ipp-sidra",
            allowed_use_scope="collect;store;internal_display_pending_x",
        )
    }
    with pytest.raises(UseNotApprovedError):
        mdq.list_producer_price_observations(
            series_id="ipp-metalurgia-index",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            limit_raw=None,
            cursor_raw=None,
        )
