"""World Bank Pink Sheet provider — workbook parsing (PROC-0076).

The fixture reproduces the real layout verified against the published
file: "Monthly Prices" sheet, commodity names on one header row, units
on the next, ``YYYYMmm`` keys in column A, ``…`` for missing values.
"""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.application.contracts import (
    InvalidResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.infrastructure.providers.worldbank_pinksheet_provider import (
    WorldBankPinkSheetProvider,
)
import requests


def _workbook_bytes(rows) -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Monthly Prices"
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


FIXTURE_ROWS = [
    ("World Bank Commodity Price Data (The Pink Sheet)", None, None, None),
    ("monthly prices in nominal US dollars, 1960 to present",) + (None,) * 3,
    (None,) * 4,
    (None,) * 4,
    (None, "Copper", "Aluminum", "Zinc"),
    (None, "($/mt)", "($/mt)", "($/mt)"),
    ("2026M01", 9100.5, 2500.25, "…"),
    ("2026M02", 9200.0, None, 2700.5),
    ("2026M03", 0, -1, 2800.0),  # non-positive → skipped, never stored
]


def _resp(status=200, body=b"", headers=None):
    class _R:
        def __init__(self):
            self.status_code = status
            self.headers = headers or {}
            self.content = body

        def json(self):
            raise ValueError("binary")

    return _R()


def _instruments():
    return [
        SimpleNamespace(
            instrument_code="copper", source_series_key="Copper"
        ),
        SimpleNamespace(
            instrument_code="aluminum", source_series_key="Aluminum"
        ),
        SimpleNamespace(instrument_code="zinc", source_series_key="Zinc"),
    ]


def _provider(transport):
    return WorldBankPinkSheetProvider(
        workbook_url="https://example.test/pink.xlsx", transport=transport
    )


def test_fetch_normalizes_monthly_observations():
    body = _workbook_bytes(FIXTURE_ROWS)
    provider = _provider(lambda url, headers, timeout: _resp(200, body))
    rows = provider.fetch_period(
        _instruments(), date(2026, 1, 1), date(2026, 12, 31)
    )
    by = {(r["instrument_code"], r["observation_date"]): r["price"] for r in rows}
    assert by[("copper", date(2026, 1, 1))] == Decimal("9100.5")
    assert by[("copper", date(2026, 2, 1))] == Decimal("9200")
    # "…" and blank cells are legitimate gaps — never stored.
    assert ("zinc", date(2026, 1, 1)) not in by
    assert ("aluminum", date(2026, 2, 1)) not in by
    # Non-positive values are rejected, not coerced.
    assert ("copper", date(2026, 3, 1)) not in by
    assert ("aluminum", date(2026, 3, 1)) not in by
    assert by[("zinc", date(2026, 3, 1))] == Decimal("2800")


def test_source_record_key_traces_cell():
    body = _workbook_bytes(FIXTURE_ROWS)
    provider = _provider(lambda url, headers, timeout: _resp(200, body))
    rows = provider.fetch_period(
        _instruments(), date(2026, 1, 1), date(2026, 1, 31)
    )
    copper = next(r for r in rows if r["instrument_code"] == "copper")
    assert copper["source_record_key"] == "pink-sheet:2026M01:Copper"


def test_window_filtering():
    body = _workbook_bytes(FIXTURE_ROWS)
    provider = _provider(lambda url, headers, timeout: _resp(200, body))
    rows = provider.fetch_period(
        _instruments(), date(2026, 2, 1), date(2026, 2, 28)
    )
    assert {r["observation_date"] for r in rows} == {date(2026, 2, 1)}


def test_missing_column_rejected():
    body = _workbook_bytes(FIXTURE_ROWS)
    provider = _provider(lambda url, headers, timeout: _resp(200, body))
    instruments = [
        SimpleNamespace(
            instrument_code="iridium", source_series_key="Iridium"
        )
    ]
    with pytest.raises(InvalidResponseError):
        provider.fetch_period(
            instruments, date(2026, 1, 1), date(2026, 12, 31)
        )


def test_unexpected_unit_rejected():
    rows = [r[:] for r in FIXTURE_ROWS]
    rows[5] = (None, "($/lb)", "($/mt)", "($/mt)")
    body = _workbook_bytes(rows)
    provider = _provider(lambda url, headers, timeout: _resp(200, body))
    instruments = [
        SimpleNamespace(
            instrument_code="copper", source_series_key="Copper"
        )
    ]
    with pytest.raises(InvalidResponseError):
        provider.fetch_period(
            instruments, date(2026, 1, 1), date(2026, 12, 31)
        )


def test_wrong_sheet_rejected():
    import openpyxl

    wb = openpyxl.Workbook()
    wb.active.title = "Not Prices"
    buf = io.BytesIO()
    wb.save(buf)
    provider = _provider(
        lambda url, headers, timeout: _resp(200, buf.getvalue())
    )
    with pytest.raises(InvalidResponseError):
        provider.fetch_period(
            _instruments(), date(2026, 1, 1), date(2026, 12, 31)
        )


def test_corrupt_body_rejected():
    provider = _provider(
        lambda url, headers, timeout: _resp(200, b"not-xlsx")
    )
    with pytest.raises(InvalidResponseError):
        provider.fetch_period(
            _instruments(), date(2026, 1, 1), date(2026, 12, 31)
        )


def test_rate_limited_429():
    provider = _provider(
        lambda url, headers, timeout: _resp(429, b"", {"Retry-After": "10"})
    )
    with pytest.raises(RateLimitedError) as exc:
        provider.fetch_period(
            _instruments(), date(2026, 1, 1), date(2026, 12, 31)
        )
    assert exc.value.retry_after == 10


@pytest.mark.parametrize("status", [403, 500, 503])
def test_unavailable_statuses(status):
    provider = _provider(lambda url, headers, timeout: _resp(status, b""))
    with pytest.raises(ProviderUnavailableError):
        provider.fetch_period(
            _instruments(), date(2026, 1, 1), date(2026, 12, 31)
        )


def test_timeout_maps_504():
    def transport(url, headers, timeout):
        raise requests.Timeout("slow")

    provider = _provider(transport)
    with pytest.raises(ProviderTimeoutError):
        provider.fetch_period(
            _instruments(), date(2026, 1, 1), date(2026, 12, 31)
        )
