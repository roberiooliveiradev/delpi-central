from datetime import date

from app.domain.services.chat_date_range_intent_service import ChatDateRangeIntentService


def test_resolve_last_month():
    resolved = ChatDateRangeIntentService.resolve(
        "qual o cpv do mes passado",
        today=date(2026, 5, 28),
    )

    assert resolved is not None
    assert resolved.start_date == "01-04-2026"
    assert resolved.end_date == "30-04-2026"


def test_resolve_explicit_range():
    resolved = ChatDateRangeIntentService.resolve(
        "cpv de 01/01/2026 a 31/01/2026",
        today=date(2026, 5, 28),
    )

    assert resolved is not None
    assert resolved.start_date == "01-01-2026"
    assert resolved.end_date == "31-01-2026"


def test_resolve_last_30_days():
    resolved = ChatDateRangeIntentService.resolve(
        "otd dos ultimos 30 dias",
        today=date(2026, 5, 28),
    )

    assert resolved is not None
    assert resolved.start_date == "29-04-2026"
    assert resolved.end_date == "28-05-2026"
