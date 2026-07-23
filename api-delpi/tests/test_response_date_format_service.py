from datetime import date

from app.application.services.response_date_format_service import (
    ResponseDateFormatService,
)


def test_format_date_accepts_ymd_br_and_iso() -> None:
    assert ResponseDateFormatService.format_date("20260723") == "2026-07-23"
    assert ResponseDateFormatService.format_date("23/07/2026") == "2026-07-23"
    assert ResponseDateFormatService.format_date("2026-07-23") == "2026-07-23"
    assert ResponseDateFormatService.format_date(date(2026, 7, 23)) == "2026-07-23"
    assert ResponseDateFormatService.format_date(None) is None
    assert ResponseDateFormatService.format_date("") is None


def test_format_payload_dates_and_period() -> None:
    payload = ResponseDateFormatService.format_payload_dates(
        {"start_date": "20260701", "sale_number": "1"},
        ("start_date",),
    )
    assert payload == {"start_date": "2026-07-01", "sale_number": "1"}

    period = ResponseDateFormatService.format_period_dict(
        {"start": "20260701", "end": "20260731"}
    )
    assert period == {"start": "2026-07-01", "end": "2026-07-31"}
