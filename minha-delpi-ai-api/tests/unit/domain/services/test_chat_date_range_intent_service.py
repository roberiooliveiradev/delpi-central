from datetime import date

from app.domain.services.chat_date_range_intent_service import ChatDateRangeIntentService
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)


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


def test_resolve_named_month_in_current_year():
    resolved = ChatDateRangeIntentService.resolve(
        "rol do mes de marco",
        today=date(2026, 5, 29),
    )

    assert resolved is not None
    assert resolved.start_date == "01-03-2026"
    assert resolved.end_date == "31-03-2026"


def test_named_month_without_year_is_ambiguous_before_month_occurs():
    ambiguous = ChatDateRangeIntentService.detect_ambiguous_named_month(
        "rol do mes de marco",
        today=date(2026, 1, 15),
    )

    assert ambiguous is not None
    assert ambiguous.current_year == 2026
    assert ambiguous.previous_year == 2025

    resolved = ChatDateRangeIntentService.resolve(
        "rol do mes de marco",
        today=date(2026, 1, 15),
    )

    assert resolved is None


def test_year_follow_up_resolves_pending_month():
    history = [{"role": "user", "content": "rol do mes de marco"}]

    resolved = ChatDateRangeIntentService.resolve(
        "2026",
        today=date(2026, 1, 15),
        previous_messages=history,
    )

    assert resolved is not None
    assert resolved.start_date == "01-03-2026"
    assert resolved.end_date == "31-03-2026"


def test_operational_parameter_asks_year_when_ambiguous():
    answer = ChatOperationalParameterService.resolve_ambiguous_period_answer(
        "rol do mes de marco",
        previous_messages=[],
        today=date(2026, 1, 15),
    )

    assert answer
    assert "2026" in answer
    assert "2025" in answer


def test_operational_parameter_skips_clarification_for_year_reply():
    history = [{"role": "user", "content": "rol do mes de marco"}]

    answer = ChatOperationalParameterService.resolve_ambiguous_period_answer(
        "desse ano",
        previous_messages=history,
    )

    assert answer is None
