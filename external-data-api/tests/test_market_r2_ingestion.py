"""R2 ingestion — Comex + IPP feeds: guards, idempotency, outcomes."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.application.market_data_ingestion import (
    MarketDataIngestionService,
    NoApprovedSeriesError,
)
from app.domain.market_data import FEED_COMEX_MONTHLY, FEED_IPP_MONTHLY
from app.infrastructure.config.settings import Settings


@pytest.fixture(autouse=True)
def _feeds_enabled(monkeypatch):
    monkeypatch.setattr(
        Settings, "EXTERNAL_DATA_FEED_COMEX_MONTHLY_ENABLED", True
    )
    monkeypatch.setattr(
        Settings, "EXTERNAL_DATA_FEED_IPP_MONTHLY_ENABLED", True
    )
from app.infrastructure.providers.comex_csv_normalizer import (
    MonthlyImportAggregate,
)
from app.infrastructure.providers.comex_import_provider import (
    ComexFetchResult,
)


def _source(active=True, scope="collect;store;derive;internal_display"):
    return SimpleNamespace(
        source_id="mdic-comex-stat",
        provider_id="mdic-comex-stat",
        source_kind="file",
        attribution="MDIC",
        license_reference="open-data",
        license_reviewed_at=date(2026, 10, 27),
        allowed_use_scope=scope,
        active=active,
    )


class FakeRepo:
    def __init__(self, **kw):
        self.kw = kw
        self.comex_upserts = []
        self.ipp_upserts = []

    def try_advisory_lock(self, key):
        return True

    def release_advisory_lock(self, key):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass

    def get_source(self, source_id):
        return self.kw.get("sources", {}).get(source_id)

    def list_ncm_allowlist(self):
        return self.kw.get("ncms", [])

    def upsert_comex_observation(self, **kw):
        self.comex_upserts.append(kw)
        return self.kw.get("comex_outcome", "inserted")

    def list_producer_price_series(self):
        return self.kw.get("series", [])

    def upsert_producer_price_observation(self, **kw):
        self.ipp_upserts.append(kw)
        return self.kw.get("ipp_outcome", "inserted")

    def create_ingestion_run(self, **kw):
        return "run-1"

    def finish_ingestion_run(self, run_id, **kw):
        self.finished = (run_id, kw)


def _agg(**over):
    base = dict(
        reference_month=date(2026, 8, 1),
        ncm_code="12345678",
        country_code="160",
        state_code="SC",
        fob_usd_total=Decimal("14000"),
        net_weight_kg_total=Decimal("4000"),
        contributing_rows=2,
        unit_value_usd_per_t=Decimal("3500"),
        quality_status="validated",
    )
    base.update(over)
    return MonthlyImportAggregate(**base)


def _comex_provider(aggs):
    class P:
        def fetch_year(self, year, *, approved_ncm_codes):
            return ComexFetchResult(
                dataset_year=year,
                source_checksum="deadbeef",
                bytes_read=100,
                aggregates=list(aggs),
            )

    return P()


def _ipp_provider(rows):
    class P:
        def fetch_series(self, **kw):
            return list(rows)

    return P()


def _service(repo, **providers):
    providers.setdefault("clock", lambda: None)
    return MarketDataIngestionService(repository=repo, **providers)


def test_comex_empty_allowlist_blocks_feed():
    repo = FakeRepo(sources={"mdic-comex-stat": _source()}, ncms=[])
    service = _service(repo, comex_provider=_comex_provider([_agg()]))
    result = service.run(
        FEED_COMEX_MONTHLY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_NO_APPROVED_SERIES"
    assert repo.comex_upserts == []


def test_comex_ingests_only_approved_ncm():
    repo = FakeRepo(
        sources={"mdic-comex-stat": _source()},
        ncms=[
            {
                "ncm_code": "12345678",
                "ncm_version": "NCM2022",
                "active": True,
            }
        ],
    )
    service = _service(repo, comex_provider=_comex_provider([_agg()]))
    result = service.run(
        FEED_COMEX_MONTHLY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    assert result.outcome == "success"
    assert result.inserted_count == 1
    assert repo.comex_upserts[0]["ncm_code"] == "12345678"
    assert repo.comex_upserts[0]["source_checksum"] == "deadbeef"


def test_comex_unlicensed_source_blocks():
    repo = FakeRepo(
        sources={
            "mdic-comex-stat": _source(
                scope="internal_display"  # no collect/store grant
            )
        },
        ncms=[{"ncm_code": "12345678", "ncm_version": "v", "active": True}],
    )
    service = _service(repo, comex_provider=_comex_provider([_agg()]))
    result = service.run(
        FEED_COMEX_MONTHLY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_SOURCE_NOT_LICENSED"


def test_ipp_ingests_active_series():
    repo = FakeRepo(
        sources={"ibge-ipp-sidra": _source()},
        series=[
            {
                "series_id": "ipp-metalurgia-index",
                "table_code": "6903",
                "classification_code": "842",
                "variable_code": "10008",
                "activity_code": "46641",
                "active": True,
            }
        ],
    )
    provider = _ipp_provider(
        [
            {
                "reference_month": date(2026, 8, 1),
                "value": Decimal("184.02"),
                "source_record_key": "sidra:10008:46641:202608",
            }
        ]
    )
    service = _service(repo, ipp_provider=provider)
    result = service.run(
        FEED_IPP_MONTHLY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    assert result.outcome == "success"
    assert result.inserted_count == 1
    assert repo.ipp_upserts[0]["series_id"] == "ipp-metalurgia-index"
    assert repo.ipp_upserts[0]["value"] == Decimal("184.02")


def test_ipp_empty_series_blocks():
    repo = FakeRepo(sources={"ibge-ipp-sidra": _source()}, series=[])
    service = _service(repo, ipp_provider=_ipp_provider([]))
    result = service.run(
        FEED_IPP_MONTHLY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_NO_APPROVED_SERIES"


def test_ipp_outside_window_skipped():
    repo = FakeRepo(
        sources={"ibge-ipp-sidra": _source()},
        series=[
            {
                "series_id": "s1",
                "table_code": "6903",
                "classification_code": "842",
                "variable_code": "10008",
                "activity_code": "46641",
                "active": True,
            }
        ],
    )
    provider = _ipp_provider(
        [
            {
                "reference_month": date(2025, 1, 1),
                "value": Decimal("1"),
                "source_record_key": "k",
            }
        ]
    )
    service = _service(repo, ipp_provider=provider)
    result = service.run(
        FEED_IPP_MONTHLY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    assert result.outcome == "success"
    assert result.inserted_count == 0
    assert result.skipped_count == 1
