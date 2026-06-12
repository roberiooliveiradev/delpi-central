import pytest

from app.infrastructure.persistence.totvs.protheus_datetime import (
    parse_protheus_period_end,
    parse_protheus_period_start,
)


def test_parse_protheus_period_start_from_datetime_local():
    assert parse_protheus_period_start("2026-06-12T10:51") == ("20260612", "10:51")
    assert parse_protheus_period_start("2026-06-12T10:51:00") == ("20260612", "10:51")


def test_parse_protheus_period_end_from_date_only_uses_end_of_day():
    assert parse_protheus_period_end("2026-06-12") == ("20260612", "23:59")


def test_parse_protheus_period_start_from_date_only_uses_start_of_day():
    assert parse_protheus_period_start("2026-06-12") == ("20260612", "00:00")


def test_parse_protheus_period_rejects_empty_value():
    with pytest.raises(ValueError):
        parse_protheus_period_start("")
