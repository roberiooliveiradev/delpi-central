from datetime import date

from app.domain.services.chat_date_range_intent_service import ChatDateRangeIntentService
from app.domain.services.chat_temporal_intent_service import ChatTemporalIntentService


def test_resolve_agora_as_today():
    resolved = ChatTemporalIntentService.resolve_point(
        "status fabril do produto 90269002 agora",
        today=date(2026, 6, 9),
        default_today=False,
    )

    assert resolved is not None
    assert resolved.target_date == date(2026, 6, 9)
    assert resolved.label == "hoje"


def test_resolve_yesterday():
    resolved = ChatTemporalIntentService.resolve_point(
        "o que foi produzido ontem?",
        today=date(2026, 5, 29),
        default_today=False,
    )

    assert resolved is not None
    assert resolved.target_date == date(2026, 5, 28)
    assert resolved.label == "ontem"


def test_resolve_day_before_yesterday():
    resolved = ChatTemporalIntentService.resolve_point(
        "programacao de antes de ontem",
        today=date(2026, 5, 29),
        default_today=False,
    )

    assert resolved is not None
    assert resolved.target_date == date(2026, 5, 27)
    assert resolved.label == "antes de ontem"


def test_resolve_slash_date_dmy():
    resolved = ChatTemporalIntentService.resolve_point(
        "producao em 03/06/2026",
        today=date(2026, 5, 29),
        default_today=False,
    )

    assert resolved is not None
    assert resolved.target_date == date(2026, 6, 3)


def test_resolve_dash_date_dmy():
    resolved = ChatTemporalIntentService.resolve_point(
        "producao em 03-06-2026",
        today=date(2026, 5, 29),
        default_today=False,
    )

    assert resolved.target_date == date(2026, 6, 3)


def test_resolve_iso_ymd():
    resolved = ChatTemporalIntentService.resolve_point(
        "producao em 2026/03/06",
        today=date(2026, 5, 29),
        default_today=False,
    )

    assert resolved.target_date == date(2026, 3, 6)


def test_resolve_named_day_month_year():
    resolved = ChatTemporalIntentService.resolve_point(
        "producao no dia 03 de junho de 2026",
        today=date(2026, 5, 29),
        default_today=False,
    )

    assert resolved.target_date == date(2026, 6, 3)
    assert "junho" in resolved.label


def test_resolve_last_monday():
    resolved = ChatTemporalIntentService.resolve_point(
        "producao na segunda passada",
        today=date(2026, 5, 29),
        default_today=False,
    )

    assert resolved is not None
    assert resolved.target_date.weekday() == 0
    assert resolved.target_date < date(2026, 5, 29)


def test_has_temporal_reference_detects_month_range_phrase():
    assert ChatTemporalIntentService.has_temporal_reference("cpv do mes que vem")


def test_date_range_last_week_calendar():
    resolved = ChatDateRangeIntentService.resolve(
        "cpv da semana passada",
        today=date(2026, 5, 29),
    )

    assert resolved is not None
    assert resolved.start_date == "18-05-2026"
    assert resolved.end_date == "24-05-2026"


def test_date_range_next_month():
    resolved = ChatDateRangeIntentService.resolve(
        "rol do mes que vem",
        today=date(2026, 5, 29),
    )

    assert resolved is not None
    assert resolved.start_date == "01-06-2026"
    assert resolved.end_date == "30-06-2026"


def test_date_range_yesterday_for_metric():
    resolved = ChatDateRangeIntentService.resolve(
        "cpv de ontem",
        today=date(2026, 5, 29),
    )

    assert resolved is not None
    assert resolved.start_date == "28-05-2026"
    assert resolved.end_date == "28-05-2026"
