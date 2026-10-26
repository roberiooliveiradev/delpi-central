"""Ingestion use case — guards, idempotency, honest outcomes (PROC-0076)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.application.contracts import (
    ProviderUnavailableError,
    SourceNotLicensedError,
)
from app.application.market_data_ingestion import (
    FeedDisabledError,
    IngestionLockedError,
    MarketDataIngestionService,
)
from app.domain.market_data import FEED_FX_DAILY, FEED_METALS_MONTHLY
from app.infrastructure.config.settings import Settings


def _source(active=True):
    return SimpleNamespace(
        source_id="bcb-ptax",
        provider_id="bcb-ptax",
        source_kind="api",
        attribution="BCB PTAX",
        license_reference="ODbL-1.0",
        license_reviewed_at=date(2026, 10, 26),
        allowed_use_scope="collect;store;derive;internal_display",
        active=active,
    )


def _instrument():
    return SimpleNamespace(
        instrument_id=7,
        instrument_code="copper",
        metal_code="copper",
        label="Cobre",
        market="world_bank_pink_sheet",
        quotation_basis="monthly_average",
        native_currency="USD",
        unit_code="metric_ton",
        unit_label="USD/metric ton",
        source_id="world-bank-pink-sheet",
        source_series_key="Copper",
        granularity="month",
        active=True,
    )


class FakeRepo:
    def __init__(self, **kw):
        self.kw = kw
        self.committed = 0
        self.runs = []
        self.upserts = []
        self.locked = True

    def try_advisory_lock(self, key):
        return self.kw.get("lock_ok", True)

    def release_advisory_lock(self, key):
        pass

    def commit(self):
        self.committed += 1

    def rollback(self):
        pass

    def get_source(self, source_id):
        sources = self.kw.get("sources", {})
        return sources.get(source_id)

    def list_instruments(self):
        return self.kw.get("instruments", [])

    def create_ingestion_run(self, **kw):
        self.runs.append(kw)
        return "run-1"

    def finish_ingestion_run(self, run_id, **kw):
        self.finished = (run_id, kw)

    def upsert_metal_observation(self, **kw):
        self.upserts.append(("metal", kw))
        return self.kw.get("upsert_outcomes", ["inserted"])[
            (len(self.upserts) - 1) % len(self.kw.get("upsert_outcomes", ["inserted"]))
        ]

    def upsert_fx_observation(self, **kw):
        self.upserts.append(("fx", kw))
        return self.kw.get("fx_outcomes", ["inserted"])[
            (len(self.upserts) - 1) % len(self.kw.get("fx_outcomes", ["inserted"]))
        ]


class FakeFxProvider:
    def __init__(self, rows=None, exc=None):
        self.rows = rows or []
        self.exc = exc

    def fetch_period(self, date_from, date_to):
        if self.exc:
            raise self.exc
        return self.rows

    @staticmethod
    def to_observations(rows, *, source_id, retrieved_at):
        out = []
        for r in rows:
            for kind, key in (
                ("ptax_closing_buy", "buy"),
                ("ptax_closing_sell", "sell"),
            ):
                out.append(
                    {
                        "pair_code": "USD/BRL",
                        "rate_kind": kind,
                        "reference_date": r["reference_date"],
                        "value": r[key],
                        "source_id": source_id,
                        "source_record_key": f"ptax:{r['reference_date']}",
                        "retrieved_at": retrieved_at,
                    }
                )
        return out


class FakeMetalsProvider:
    def __init__(self, rows=None, exc=None):
        self.rows = rows or []
        self.exc = exc

    def fetch_period(self, instruments, date_from, date_to):
        if self.exc:
            raise self.exc
        return self.rows


def _enable(monkeypatch, feed):
    if feed == FEED_FX_DAILY:
        monkeypatch.setattr(Settings, "EXTERNAL_DATA_FEED_FX_DAILY_ENABLED", True)
    else:
        monkeypatch.setattr(
            Settings, "EXTERNAL_DATA_FEED_METALS_MONTHLY_ENABLED", True
        )


def test_disabled_feed_refuses(monkeypatch):
    service = MarketDataIngestionService(repository=FakeRepo())
    with pytest.raises(FeedDisabledError):
        service.run(
            FEED_FX_DAILY,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
        )


def test_unlicensed_source_fails_run(monkeypatch):
    _enable(monkeypatch, FEED_FX_DAILY)
    repo = FakeRepo(sources={"bcb-ptax": _source(active=False)})
    service = MarketDataIngestionService(
        repository=repo, fx_provider=FakeFxProvider()
    )
    result = service.run(
        FEED_FX_DAILY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_SOURCE_NOT_LICENSED"
    assert repo.upserts == []


def test_missing_source_fails_run(monkeypatch):
    _enable(monkeypatch, FEED_FX_DAILY)
    repo = FakeRepo(sources={})
    service = MarketDataIngestionService(
        repository=repo, fx_provider=FakeFxProvider()
    )
    result = service.run(
        FEED_FX_DAILY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_SOURCE_NOT_LICENSED"


def test_fx_run_upserts_buy_and_sell(monkeypatch):
    _enable(monkeypatch, FEED_FX_DAILY)
    repo = FakeRepo(sources={"bcb-ptax": _source()})
    rows = [
        {
            "reference_date": date(2026, 1, 5),
            "buy": Decimal("5.41"),
            "sell": Decimal("5.42"),
        }
    ]
    service = MarketDataIngestionService(
        repository=repo, fx_provider=FakeFxProvider(rows=rows)
    )
    result = service.run(
        FEED_FX_DAILY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
    )
    assert result.outcome == "success"
    assert result.inserted_count == 2
    kinds = {u[1]["rate_kind"] for u in repo.upserts}
    assert kinds == {"ptax_closing_buy", "ptax_closing_sell"}


def test_fx_provider_failure_marks_failed(monkeypatch):
    _enable(monkeypatch, FEED_FX_DAILY)
    repo = FakeRepo(sources={"bcb-ptax": _source()})
    service = MarketDataIngestionService(
        repository=repo,
        fx_provider=FakeFxProvider(
            exc=ProviderUnavailableError("ptax down")
        ),
    )
    result = service.run(
        FEED_FX_DAILY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_PROVIDER_UNAVAILABLE"
    assert repo.finished[1]["safe_error_code"] == (
        "EXTERNAL_DATA_PROVIDER_UNAVAILABLE"
    )


def test_idempotent_second_run_skips_unchanged(monkeypatch):
    _enable(monkeypatch, FEED_FX_DAILY)
    repo = FakeRepo(
        sources={"bcb-ptax": _source()}, fx_outcomes=["unchanged"]
    )
    rows = [
        {
            "reference_date": date(2026, 1, 5),
            "buy": Decimal("5.41"),
            "sell": Decimal("5.42"),
        }
    ]
    service = MarketDataIngestionService(
        repository=repo, fx_provider=FakeFxProvider(rows=rows)
    )
    result = service.run(
        FEED_FX_DAILY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
    )
    assert result.outcome == "success"
    assert result.inserted_count == 0
    assert result.skipped_count == 2


def test_lock_contention_refuses(monkeypatch):
    _enable(monkeypatch, FEED_FX_DAILY)
    repo = FakeRepo(lock_ok=False)
    service = MarketDataIngestionService(
        repository=repo, fx_provider=FakeFxProvider()
    )
    with pytest.raises(IngestionLockedError):
        service.run(
            FEED_FX_DAILY,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
        )


def test_metals_run_uses_instrument_identity(monkeypatch):
    _enable(monkeypatch, FEED_METALS_MONTHLY)
    wb_source = _source()
    wb_source.source_id = "world-bank-pink-sheet"
    wb_source.provider_id = "world-bank-pink-sheet"
    repo = FakeRepo(
        sources={"world-bank-pink-sheet": wb_source},
        instruments=[_instrument()],
    )
    rows = [
        {
            "instrument_code": "copper",
            "observation_date": date(2026, 9, 1),
            "price": Decimal("9500.5"),
            "source_record_key": "pink-sheet:2026M09:Copper",
        },
        {
            "instrument_code": "unknown-metal",  # not in catalog → skip
            "observation_date": date(2026, 9, 1),
            "price": Decimal("1"),
        },
    ]
    service = MarketDataIngestionService(
        repository=repo, metals_provider=FakeMetalsProvider(rows=rows)
    )
    result = service.run(
        FEED_METALS_MONTHLY,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    assert result.outcome == "success"
    assert result.inserted_count == 1
    assert result.skipped_count == 1
    assert repo.upserts[0][1]["native_price"] == Decimal("9500.5")
    assert repo.upserts[0][1]["quote_basis"] == "monthly_average"
