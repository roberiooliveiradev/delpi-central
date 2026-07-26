"""Testes do dual-read canônico start_date/end_date."""

from __future__ import annotations

from app.interface.http.period_query_params import resolve_period_dates


def test_canonical_wins_over_legacy():
    start, end = resolve_period_dates(
        start_date="2026-01-01",
        end_date="2026-01-31",
        date_start="2025-01-01",
        date_end="2025-01-31",
    )
    assert start == "2026-01-01"
    assert end == "2026-01-31"


def test_date_start_alias():
    start, end = resolve_period_dates(date_start="2026-07-01", date_end="2026-07-15")
    assert start == "2026-07-01"
    assert end == "2026-07-15"


def test_dataInicio_alias():
    start, end = resolve_period_dates(dataInicio="2026-03-01", dataFim="2026-03-31")
    assert start == "2026-03-01"
    assert end == "2026-03-31"


def test_empty_strings_ignored():
    start, end = resolve_period_dates(
        start_date="",
        end_date="  ",
        date_start="2026-02-01",
        date_end="2026-02-28",
    )
    assert start == "2026-02-01"
    assert end == "2026-02-28"


def test_none_when_absent():
    assert resolve_period_dates() == (None, None)
