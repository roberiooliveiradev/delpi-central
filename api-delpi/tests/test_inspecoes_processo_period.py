from datetime import date

import pytest

from app.domain.quality.inspecoes_processo.inspecoes_processo_period import (
    lookback_floor,
    period_repository_kwargs,
    resolve_optional_period,
)


def test_resolve_optional_period_returns_none_when_empty() -> None:
    assert resolve_optional_period(None, None) == (None, None)
    assert resolve_optional_period("", "  ") == (None, None)


def test_resolve_optional_period_rejects_inverted_range() -> None:
    with pytest.raises(ValueError, match="start_date não pode ser maior"):
        resolve_optional_period("2026-08-14", "2026-08-01")


def test_resolve_optional_period_clamps_start_to_lookback() -> None:
    start, end = resolve_optional_period(
        "2020-01-01",
        "2026-08-14",
        today=date(2026, 8, 14),
    )
    assert start == lookback_floor(date(2026, 8, 14))
    assert end == "2026-08-14"


def test_resolve_optional_period_fills_start_when_only_end() -> None:
    start, end = resolve_optional_period(
        None,
        "2026-08-14",
        today=date(2026, 8, 14),
    )
    assert start == "2025-08-14"
    assert end == "2026-08-14"


def test_period_repository_kwargs_omits_when_empty() -> None:
    assert period_repository_kwargs(None, None) == {}
    assert period_repository_kwargs("2026-08-01", "2026-08-14") == {
        "start_date": "2026-08-01",
        "end_date": "2026-08-14",
    }
