"""Testes da classificação canônica de turnos de fábrica."""

import pytest

from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.production.factory_shifts import (
    FACTORY_SHIFTS,
    FACTORY_TIMEZONE,
    current_factory_shift,
    describe_factory_shifts,
    factory_shift_id,
    factory_shift_label,
    matches_factory_shift_filter,
    parse_factory_shift_filter,
    parse_start_time_to_minutes,
    resolve_factory_shift,
)


@pytest.mark.parametrize(
    ("hora", "expected_id", "expected_label"),
    [
        ("04:34", "1", "1º Turno"),
        ("10:00", "1", "1º Turno"),
        ("14:17", "1", "1º Turno"),
        ("14:18", "2", "2º Turno"),
        ("18:00:00", "2", "2º Turno"),
        ("23:49", "2", "2º Turno"),
        ("23:50", "3", "3º Turno"),
        ("00:15", "3", "3º Turno"),
        ("04:33", "3", "3º Turno"),
        ("2026-01-01T08:00:00", "1", "1º Turno"),
    ],
)
def test_resolve_factory_shift_boundaries(
    hora: str, expected_id: str, expected_label: str
) -> None:
    shift = resolve_factory_shift(hora)
    assert shift is not None
    assert shift.id == expected_id
    assert factory_shift_id(hora) == expected_id
    assert factory_shift_label(hora) == expected_label


def test_resolve_factory_shift_invalid_returns_none() -> None:
    assert resolve_factory_shift(None) is None
    assert resolve_factory_shift("") is None
    assert resolve_factory_shift("abc") is None
    assert parse_start_time_to_minutes("25:00") is None


def test_parse_factory_shift_filter_csv_and_dedupe() -> None:
    assert parse_factory_shift_filter(None) == ()
    assert parse_factory_shift_filter("1,2,1") == ("1", "2")
    assert parse_factory_shift_filter(["3", "2"]) == ("3", "2")


def test_parse_factory_shift_filter_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="shift inválido"):
        parse_factory_shift_filter("4")


def test_matches_factory_shift_filter_prefers_turno() -> None:
    assert matches_factory_shift_filter(
        "10:00",
        shifts=("2",),
        turno="2",
    )
    assert not matches_factory_shift_filter(
        "10:00",
        shifts=("2",),
        turno="1",
    )
    assert matches_factory_shift_filter("10:00", shifts=("1",), turno=None)
    assert matches_factory_shift_filter("10:00", shifts=())


def _at(hour: int, minute: int) -> datetime:
    return datetime(2026, 9, 14, hour, minute, tzinfo=ZoneInfo(FACTORY_TIMEZONE))


@pytest.mark.parametrize(
    ("moment", "expected_id"),
    [
        (_at(10, 0), "1"),
        (_at(18, 0), "2"),
        (_at(2, 0), "3"),
    ],
)
def test_current_factory_shift_uses_the_same_boundaries(moment, expected_id) -> None:
    shift = current_factory_shift(moment)
    assert shift is not None
    assert shift.id == expected_id


def test_describe_factory_shifts_exposes_catalog_and_current() -> None:
    payload = describe_factory_shifts(_at(18, 0))

    assert payload["timezone"] == FACTORY_TIMEZONE
    assert payload["current_shift_id"] == "2"
    assert payload["current_shift"]["label"] == "2º Turno"
    assert payload["reference_time"].startswith("2026-09-14T18:00")
    assert [shift["id"] for shift in payload["shifts"]] == ["1", "2", "3"]
    assert payload["shifts"][0] == {
        "id": FACTORY_SHIFTS[0].id,
        "label": FACTORY_SHIFTS[0].label,
        "start_time": FACTORY_SHIFTS[0].start,
        "end_time": FACTORY_SHIFTS[0].end,
    }
