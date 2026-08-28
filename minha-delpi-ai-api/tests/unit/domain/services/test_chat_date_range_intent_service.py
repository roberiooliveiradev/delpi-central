from datetime import date

from app.domain.services.chat_date_range_intent_service import ChatDateRangeIntentService
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)


def test_resolve_hoje_as_single_day_range():
    resolved = ChatDateRangeIntentService.resolve(
        "qual a eficiencia fabril de hoje?",
        today=date(2026, 6, 1),
    )

    assert resolved is not None
    assert resolved.start_date == "01-06-2026"
    assert resolved.end_date == "01-06-2026"


def test_resolve_desse_mes_as_current_month():
    resolved = ChatDateRangeIntentService.resolve(
        "qual a meta para comercial desse mês?",
        today=date(2026, 7, 20),
    )

    assert resolved is not None
    assert resolved.start_date == "01-07-2026"
    assert resolved.end_date == "31-07-2026"


def test_resolve_dia_atual_as_single_day_range():
    resolved = ChatDateRangeIntentService.resolve(
        "oee do dia atual",
        today=date(2026, 6, 1),
    )

    assert resolved is not None
    assert resolved.start_date == resolved.end_date == "01-06-2026"


def test_resolve_esta_semana_calendar_range():
    resolved = ChatDateRangeIntentService.resolve(
        "faturamento desta semana",
        today=date(2026, 6, 4),
    )

    assert resolved is not None
    assert resolved.start_date == "01-06-2026"
    assert resolved.end_date == "07-06-2026"


def test_resolve_essa_semana_calendar_range():
    resolved = ChatDateRangeIntentService.resolve(
        "status fabril do produto 90261892 essa semana",
        today=date(2026, 6, 9),
    )

    assert resolved is not None
    assert resolved.start_date == "08-06-2026"
    assert resolved.end_date == "14-06-2026"


def test_resolve_trimestre_passado():
    resolved = ChatDateRangeIntentService.resolve(
        "ebitda do trimestre passado",
        today=date(2026, 6, 1),
    )

    assert resolved is not None
    assert resolved.start_date == "01-01-2026"
    assert resolved.end_date == "31-03-2026"


def test_resolve_ultimas_duas_semanas():
    resolved = ChatDateRangeIntentService.resolve(
        "otd das ultimas 2 semanas",
        today=date(2026, 6, 1),
    )

    assert resolved is not None
    assert resolved.start_date == "19-05-2026"
    assert resolved.end_date == "01-06-2026"


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


def test_resolve_inherits_period_from_previous_user_message():
    resolved = ChatDateRangeIntentService.resolve(
        "somente da filial 01",
        today=date(2026, 8, 28),
        previous_messages=[
            {"role": "user", "content": "qual o rol desse mês?"},
            {"role": "assistant", "content": "Aqui está o ROL."},
        ],
    )

    assert resolved is not None
    assert resolved.start_date == "01-08-2026"
    assert resolved.end_date == "31-08-2026"
    assert "histórico" in resolved.reason.lower()


def test_build_date_branch_merge_branch_keeps_inherited_august_dates():
    from app.domain.services.operational_api_parameter_builder_service import (
        OperationalApiParameterBuilderService,
    )

    builder = OperationalApiParameterBuilderService()
    # Período já resolvido (DateRangeIntent/histórico); merge só aplica filial.
    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "branch", "in": "query"},
                {"name": "start_date", "in": "query"},
                {"name": "end_date", "in": "query"},
            ],
        },
        "somente da filial 01",
        base_params={
            "start_date": "01-08-2026",
            "end_date": "31-08-2026",
            "branch": "all",
        },
    )

    assert parameters["branch"] == "01"
    assert parameters["start_date"] == "01-08-2026"
    assert parameters["end_date"] == "31-08-2026"
