"""Market intelligence service — freshness cadence and unit semantics
(PROC-0076 R1).

Deterministic dates: ``FrozenDate`` patches the module-level ``date``
symbol so ``date.today()`` is controlled while ``date.fromisoformat`` and
arithmetic keep working.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.application.services import market_intelligence_service as svc_module
from app.application.services.market_intelligence_service import (
    MarketIntelligenceService,
)


def _frozen(today: date):
    class FrozenDate(date):
        @classmethod
        def today(cls) -> date:
            return today

    return patch.object(svc_module, "date", FrozenDate)


def _catalog(*, metal_latest="2026-09-01", fx_latest="2026-10-23") -> dict:
    return {
        "instruments": [
            {
                "instrument_code": "copper",
                "kind": "metal",
                "label": "Cobre",
                "quote_basis": "monthly_average",
                "currency": "USD",
                "unit_code": "metric_ton",
                "unit": "USD/metric ton",
                "granularity": "month",
                "source_id": "world-bank-pink-sheet",
                "latest_observation_date": metal_latest,
            }
        ],
        "fx_series": [
            {
                "instrument_code": "usd-brl",
                "kind": "fx",
                "label": "Dólar / Real",
                "pair": "USD/BRL",
                "rate_kinds": ["ptax_closing_sell"],
                "currency": "BRL",
                "unit": "BRL per USD",
                "granularity": "day",
                "source_id": "bcb-ptax",
                "latest_observation_date": fx_latest,
            }
        ],
        "sources": [],
        "meta": {"schema_version": "v1"},
    }


def _metal(months: list[tuple[str, str]]) -> list[dict]:
    return [
        {
            "instrument_code": "copper",
            "observation_date": f"{month}-01",
            "price": price,
            "currency": "USD",
            "unit": "USD/metric ton",
            "quality": "validated",
            "source": {"source_id": "world-bank-pink-sheet"},
        }
        for month, price in months
    ]


def _fx(days: list[tuple[str, str]]) -> list[dict]:
    return [
        {
            "pair": "USD/BRL",
            "rate_kind": "ptax_closing_sell",
            "reference_date": day,
            "value": value,
            "quality": "validated",
            "source": {"source_id": "bcb-ptax"},
        }
        for day, value in days
    ]


def _service(
    *, metal=None, fx=None, metal_latest="2026-09-01", fx_latest="2026-10-23"
) -> MarketIntelligenceService:
    gateway = MagicMock()
    gateway.catalog.return_value = _catalog(
        metal_latest=metal_latest, fx_latest=fx_latest
    )
    gateway.ingestion_status.return_value = {"feeds": []}
    gateway.metal_observations.return_value = metal or []
    gateway.fx_observations.return_value = fx or []
    return MarketIntelligenceService(gateway=gateway)


# --- freshness: window vs feed cadence (R1.S1) -------------------------------


def test_historical_complete_window_is_not_stale():
    """AC-R1-01: a fully covered 2024 query is ``ok`` — the period ending
    months ago does not make it stale when the feed is current."""
    service = _service(
        metal=_metal(
            [(f"2024-{m:02d}", "9000") for m in range(1, 7)]
        ),
        metal_latest="2026-09-01",
    )
    with _frozen(date(2026, 10, 26)):
        result = service.get_summary(
            instrument_code="copper",
            currency="USD",
            fx_kind="ptax_closing_sell",
            date_from="2024-01-01",
            date_to="2024-06-30",
        )
    assert result["meta"]["data_status"] == "ok"
    assert result["meta"]["freshness"]["status"] == "current"


def test_delayed_feed_reports_freshness_without_distorting_window():
    """AC-R1-02 + AC-R1.1-11/12: a fully covered window keeps its
    completeness (``ok``) even when the *feed* is behind cadence — the
    delay is reported separately in ``meta.freshness``."""
    service = _service(
        metal=_metal([(f"2026-{m:02d}", "9000") for m in range(1, 7)]),
        metal_latest="2026-06-01",  # feed stopped in June
    )
    with _frozen(date(2026, 10, 26)):
        result = service.get_summary(
            instrument_code="copper",
            currency="USD",
            fx_kind="ptax_closing_sell",
            date_from="2026-01-01",
            date_to="2026-06-30",
        )
    freshness = result["meta"]["freshness"]
    # Dimension 1 — window completeness: fully covered → ok, not stale.
    assert result["meta"]["data_status"] == "ok"
    # Dimension 2 — feed freshness: delayed, with temporal evidence.
    assert freshness["status"] == "delayed"
    assert freshness["expected_latest_period"] == "2026-09-01"
    assert freshness["latest_observation_date"] == "2026-06-01"
    assert freshness["lag_periods"] == 3


def test_incomplete_window_stays_partial_with_current_feed():
    """AC-R1.1-13: a current feed cannot manufacture completeness —
    a window missing observations is ``partial`` regardless."""
    service = _service(
        metal=_metal([("2026-08", "9000")]),  # only 1 of 2 months
        metal_latest="2026-09-01",
    )
    with _frozen(date(2026, 10, 26)):
        result = service.get_summary(
            instrument_code="copper",
            currency="USD",
            fx_kind="ptax_closing_sell",
            date_from="2026-08-01",
            date_to="2026-09-30",
        )
    assert result["meta"]["data_status"] == "partial"
    assert result["meta"]["freshness"]["status"] == "current"


def test_monthly_cadence_early_month_is_current():
    """AC-R1-03: before the ~5th, last month's data may not be published
    yet — September data on Oct 3rd is still ``current``."""
    service = _service(metal_latest="2026-09-01")
    with _frozen(date(2026, 10, 3)):
        freshness = service._freshness(
            kind="metal",
            latest_available=date(2026, 9, 1),
            feed_ingestion=None,
        )
    assert freshness["status"] == "current"
    assert freshness["expected_latest_period"] == "2026-08-01"


def test_monthly_cadence_after_publication_day():
    """AC-R1-03: after publication day the previous month is expected."""
    service = _service()
    with _frozen(date(2026, 10, 26)):
        freshness = service._freshness(
            kind="metal",
            latest_available=date(2026, 8, 1),
            feed_ingestion=None,
        )
    assert freshness["status"] == "delayed"
    assert freshness["expected_latest_period"] == "2026-09-01"


def test_fx_weekend_gap_is_not_a_failure():
    """AC: no PTAX bulletin on weekends/holidays — a Friday→Monday gap is
    within the grace and stays ``current``."""
    service = _service()
    # 2026-10-26 is a Monday; latest bulletin Friday 2026-10-23.
    with _frozen(date(2026, 10, 26)):
        freshness = service._freshness(
            kind="fx",
            latest_available=date(2026, 10, 23),
            feed_ingestion=None,
        )
    assert freshness["status"] == "current"
    assert freshness["lag_days"] == 3


def test_fx_missing_bulletins_beyond_grace_is_delayed():
    service = _service()
    with _frozen(date(2026, 10, 26)):
        freshness = service._freshness(
            kind="fx",
            latest_available=date(2026, 10, 15),
            feed_ingestion=None,
        )
    assert freshness["status"] == "delayed"


def test_no_data_window():
    service = _service(metal=[], metal_latest="2026-09-01")
    with _frozen(date(2026, 10, 26)):
        result = service.get_summary(
            instrument_code="copper",
            currency="USD",
            fx_kind="ptax_closing_sell",
            date_from="2024-01-01",
            date_to="2024-06-30",
        )
    assert result["meta"]["data_status"] == "no_data"
    assert result["last_quote"] is None


def test_missing_fx_months_is_partial_not_metal_missing():
    """AC-R1-04: FX absence is differentiated — ``partial`` with
    ``fx_missing_months`` while the metal data itself is complete."""
    service = _service(
        metal=_metal([("2026-08", "9000"), ("2026-09", "9500")]),
        fx=_fx([("2026-08-03", "5.0")]),  # September has no FX
        metal_latest="2026-09-01",
    )
    with _frozen(date(2026, 10, 26)):
        result = service.get_summary(
            instrument_code="copper",
            currency="BRL",
            fx_kind="ptax_closing_sell",
            date_from="2026-08-01",
            date_to="2026-09-30",
        )
    assert result["meta"]["data_status"] == "partial"
    assert result["meta"]["partial_reason"] == "fx_missing_months:2026-09"


# --- units: USD native vs BRL display (R1.S2) --------------------------------


def test_usd_quote_reports_native_unit():
    """AC-R1-06: USD quote is USD per metric ton."""
    service = _service(
        metal=_metal([("2026-09", "9500.5")]),
        metal_latest="2026-09-01",
    )
    with _frozen(date(2026, 10, 26)):
        result = service.get_summary(
            instrument_code="copper",
            currency="USD",
            fx_kind="ptax_closing_sell",
            date_from="2026-09-01",
            date_to="2026-09-30",
        )
    assert result["last_quote"]["value"] == "9500.5"
    assert result["last_quote"]["currency"] == "USD"
    assert result["last_quote"]["unit"] == "USD/metric ton"
    assert "native" not in result["last_quote"]


def test_brl_quote_reports_brl_unit_and_preserves_native():
    """AC-R1-07/08: converted quote is BRL per metric ton, with native
    value, FX rate and versioned method kept auditable."""
    service = _service(
        metal=_metal([("2026-09", "9500.5")]),
        fx=_fx([("2026-09-02", "6.0")]),
        metal_latest="2026-09-01",
    )
    with _frozen(date(2026, 10, 26)):
        result = service.get_summary(
            instrument_code="copper",
            currency="BRL",
            fx_kind="ptax_closing_sell",
            date_from="2026-09-01",
            date_to="2026-09-30",
        )
    last = result["last_quote"]
    assert last["unit"] == "BRL/metric ton"
    assert last["value"] == "57003.0"  # 9500.5 × 6.0
    assert last["native"] == {
        "value": "9500.5",
        "currency": "USD",
        "unit": "USD/metric ton",
    }
    assert last["conversion"]["method"] == (
        "metal_monthly_avg_x_ptax_monthly_avg/v1"
    )
    assert last["conversion"]["fx_rate"] == "6.0"
    assert last["conversion"]["fx_kind"] == "ptax_closing_sell"
    assert result["period_average"]["unit"] == "BRL/metric ton"


def test_brl_without_fx_returns_null_not_synthetic():
    """AC-R1-09 + AC-R1.1-06/08: a month without valid FX never produces
    a synthetic rate — converted values stay ``null``, and with metal
    data present the state is ``partial`` (never ``no_data``)."""
    service = _service(
        metal=_metal([("2026-09", "9500.5")]),
        fx=[],  # no FX at all
        metal_latest="2026-09-01",
    )
    with _frozen(date(2026, 10, 26)):
        result = service.get_summary(
            instrument_code="copper",
            currency="BRL",
            fx_kind="ptax_closing_sell",
            date_from="2026-09-01",
            date_to="2026-09-30",
        )
    assert result["last_quote"] is None
    assert result["meta"]["data_status"] == "partial"
    assert result["meta"]["partial_reason"] == "fx_missing_months:2026-09"

    series = service.list_series(
        instrument_code="copper",
        currency="BRL",
        granularity="month",
        fx_kind="ptax_closing_sell",
        date_from="2026-09-01",
        date_to="2026-09-30",
    )
    assert series["meta"]["data_status"] == "partial"
    assert series["meta"]["partial_reason"] == "fx_missing_months:2026-09"
    assert all(p["value"] is None for p in series["points"])

    monthly = service.list_monthly_averages(
        instrument_code="copper",
        currency="BRL",
        fx_kind="ptax_closing_sell",
        date_from="2026-09-01",
        date_to="2026-09-30",
        page=None,
        page_size=None,
    )
    row = monthly["items"][0]
    assert monthly["meta"]["data_status"] == "partial"
    assert row["average"] is None
    assert row["native_average"] == "9500.5"
    assert row["fx_rate"] is None
    assert row["coverage"] == "fx_missing"


def test_usd_query_unaffected_by_missing_fx():
    """AC-R1.1-09: USD queries never depend on FX — metal data without
    any PTAX is still ``ok``, not ``partial``/``no_data``."""
    service = _service(
        metal=_metal([("2026-08", "9000"), ("2026-09", "9500")]),
        fx=[],
        metal_latest="2026-09-01",
    )
    with _frozen(date(2026, 10, 26)):
        result = service.get_summary(
            instrument_code="copper",
            currency="USD",
            fx_kind="ptax_closing_sell",
            date_from="2026-08-01",
            date_to="2026-09-30",
        )
    assert result["meta"]["data_status"] == "ok"
    assert result["meta"]["partial_reason"] is None
    assert result["last_quote"]["value"] == "9500.0"
    assert result["last_quote"]["unit"] == "USD/metric ton"


def test_unknown_instrument_raises_not_found():
    """AC-R1.1: an instrument absent from the catalog is a 404-class
    lookup error, never a fabricated empty series."""
    from app.application.services.market_intelligence_service import (
        MarketDataNotFoundError,
    )

    service = _service()
    with pytest.raises(MarketDataNotFoundError):
        service.get_summary(
            instrument_code="unobtainium",
            currency="USD",
            fx_kind="ptax_closing_sell",
            date_from="2026-09-01",
            date_to="2026-09-30",
        )


def test_brl_partial_fx_single_month():
    """Metal present in two months, PTAX only in one → ``partial``,
    the converted month keeps a value and the missing one stays null."""
    service = _service(
        metal=_metal([("2026-08", "9000"), ("2026-09", "9500")]),
        fx=_fx([("2026-08-03", "5.0")]),
        metal_latest="2026-09-01",
    )
    with _frozen(date(2026, 10, 26)):
        series = service.list_series(
            instrument_code="copper",
            currency="BRL",
            granularity="month",
            fx_kind="ptax_closing_sell",
            date_from="2026-08-01",
            date_to="2026-09-30",
        )
    assert series["meta"]["data_status"] == "partial"
    assert series["meta"]["partial_reason"] == "fx_missing_months:2026-09"
    values = {p["period"]: p["value"] for p in series["points"]}
    assert values["2026-08"] == "45000.0"
    assert values["2026-09"] is None


def test_monetary_semantics_consistent_across_endpoints():
    """AC-R1-10: summary, series and monthly-averages expose the same
    display unit and native unit."""
    service = _service(
        metal=_metal([("2026-08", "9000"), ("2026-09", "9500")]),
        fx=_fx([("2026-08-03", "5.0"), ("2026-09-02", "6.0")]),
        metal_latest="2026-09-01",
    )
    kwargs = dict(
        instrument_code="copper",
        currency="BRL",
        fx_kind="ptax_closing_sell",
        date_from="2026-08-01",
        date_to="2026-09-30",
    )
    with _frozen(date(2026, 10, 26)):
        summary = service.get_summary(**kwargs)
        series = service.list_series(granularity="month", **kwargs)
        monthly = service.list_monthly_averages(
            page=None, page_size=None, **kwargs
        )
    assert summary["meta"]["unit"] == "BRL/metric ton"
    assert summary["meta"]["native_unit"] == "USD/metric ton"
    assert series["unit"] == "BRL/metric ton"
    assert series["native_unit"] == "USD/metric ton"
    assert monthly["unit"] == "BRL/metric ton"
    assert monthly["native_unit"] == "USD/metric ton"
    # BRL points = USD × monthly PTAX
    assert series["points"][0]["value"] == "45000.0"  # 9000 × 5
    assert series["points"][1]["value"] == "57000.0"  # 9500 × 6


def test_ptax_buy_and_sell_are_not_mixed():
    """fx_kind selects the series; buy and sell never blend."""
    service = _service(
        metal=_metal([("2026-09", "9000")]),
        fx=_fx([("2026-09-02", "6.0")]),
        metal_latest="2026-09-01",
    )
    with _frozen(date(2026, 10, 26)):
        service.get_summary(
            instrument_code="copper",
            currency="BRL",
            fx_kind="ptax_closing_sell",
            date_from="2026-09-01",
            date_to="2026-09-30",
        )
    service._gateway.fx_observations.assert_called_with(
        "ptax_closing_sell", date(2026, 9, 1), date(2026, 9, 30)
    )
