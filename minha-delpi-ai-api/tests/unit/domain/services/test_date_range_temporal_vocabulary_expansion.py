"""Regressão — variações PT-BR de dia, semana, mês, trimestre, semestre e ano."""

from __future__ import annotations

from datetime import date

import pytest

from app.domain.services.chat_date_range_intent_service import ChatDateRangeIntentService
from app.domain.services.chat_operational_date_parameter_service import (
    ChatOperationalDateParameterService,
)
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)
from app.domain.services.chat_temporal_intent_service import ChatTemporalIntentService

_REFERENCE = date(2026, 6, 9)


@pytest.mark.parametrize(
    ("message", "start_date", "end_date"),
    [
        pytest.param("cpv de hoje", "09-06-2026", "09-06-2026", id="dia-hoje"),
        pytest.param("cpv de hoje mesmo", "09-06-2026", "09-06-2026", id="dia-hoje-mesmo"),
        pytest.param("cpv de ontem", "08-06-2026", "08-06-2026", id="dia-ontem"),
        pytest.param("cpv de ontem mesmo", "08-06-2026", "08-06-2026", id="dia-ontem-mesmo"),
        pytest.param("cpv do dia de ontem", "08-06-2026", "08-06-2026", id="dia-de-ontem"),
        pytest.param("cpv de amanha", "10-06-2026", "10-06-2026", id="dia-amanha"),
        pytest.param("cpv do dia de amanha", "10-06-2026", "10-06-2026", id="dia-de-amanha"),
        pytest.param("cpv de anteontem", "07-06-2026", "07-06-2026", id="dia-anteontem"),
        pytest.param("cpv de agora", "09-06-2026", "09-06-2026", id="dia-agora"),
    ],
)
def test_day_point_variations_resolve_single_day_range(
    message: str,
    start_date: str,
    end_date: str,
):
    resolved = ChatDateRangeIntentService.resolve(message, today=_REFERENCE)

    assert resolved is not None
    assert resolved.start_date == start_date
    assert resolved.end_date == end_date


@pytest.mark.parametrize(
    ("phrase", "start_date", "end_date"),
    [
        pytest.param("essa semana", "08-06-2026", "14-06-2026", id="semana-essa"),
        pytest.param("semana passada", "01-06-2026", "07-06-2026", id="semana-passada"),
        pytest.param("semana antepassada", "25-05-2026", "31-05-2026", id="semana-antepassada"),
        pytest.param("na semana que vem", "15-06-2026", "21-06-2026", id="semana-que-vem"),
        pytest.param("daqui a duas semanas", "22-06-2026", "28-06-2026", id="semana-daqui-duas"),
        pytest.param("ultimos 7 dias", "03-06-2026", "09-06-2026", id="semana-rolling-7"),
    ],
)
def test_week_variations_resolve_date_range(phrase: str, start_date: str, end_date: str):
    resolved = ChatDateRangeIntentService.resolve(f"otd do {phrase}", today=_REFERENCE)

    assert resolved is not None
    assert resolved.start_date == start_date
    assert resolved.end_date == end_date


@pytest.mark.parametrize(
    ("phrase", "start_date", "end_date"),
    [
        pytest.param("esse mes", "01-06-2026", "30-06-2026", id="mes-esse"),
        pytest.param("mes passado", "01-05-2026", "31-05-2026", id="mes-passado"),
        pytest.param("mes que vem", "01-07-2026", "31-07-2026", id="mes-que-vem"),
        pytest.param("mes seguinte", "01-07-2026", "31-07-2026", id="mes-seguinte"),
    ],
)
def test_month_variations_resolve_date_range(phrase: str, start_date: str, end_date: str):
    resolved = ChatDateRangeIntentService.resolve(f"rol do {phrase}", today=_REFERENCE)

    assert resolved is not None
    assert resolved.start_date == start_date
    assert resolved.end_date == end_date


@pytest.mark.parametrize(
    ("phrase", "start_date", "end_date"),
    [
        pytest.param("esse trimestre", "01-04-2026", "30-06-2026", id="trimestre-esse"),
        pytest.param("trimestre passado", "01-01-2026", "31-03-2026", id="trimestre-passado"),
        pytest.param("proximo trimestre", "01-07-2026", "30-09-2026", id="trimestre-proximo"),
        pytest.param("trimestre que vem", "01-07-2026", "30-09-2026", id="trimestre-que-vem"),
    ],
)
def test_quarter_variations_resolve_date_range(phrase: str, start_date: str, end_date: str):
    resolved = ChatDateRangeIntentService.resolve(f"ebitda do {phrase}", today=_REFERENCE)

    assert resolved is not None
    assert resolved.start_date == start_date
    assert resolved.end_date == end_date


@pytest.mark.parametrize(
    ("phrase", "start_date", "end_date"),
    [
        pytest.param("esse semestre", "01-01-2026", "30-06-2026", id="semestre-esse"),
        pytest.param("semestre passado", "01-07-2025", "31-12-2025", id="semestre-passado"),
        pytest.param("proximo semestre", "01-07-2026", "31-12-2026", id="semestre-proximo"),
        pytest.param("primeiro semestre de 2025", "01-01-2025", "30-06-2025", id="semestre-1-2025"),
        pytest.param("segundo semestre de 2024", "01-07-2024", "31-12-2024", id="semestre-2-2024"),
    ],
)
def test_semester_variations_resolve_date_range(phrase: str, start_date: str, end_date: str):
    resolved = ChatDateRangeIntentService.resolve(f"faturamento do {phrase}", today=_REFERENCE)

    assert resolved is not None
    assert resolved.start_date == start_date
    assert resolved.end_date == end_date


@pytest.mark.parametrize(
    ("phrase", "start_date", "end_date"),
    [
        pytest.param("esse ano", "01-01-2026", "31-12-2026", id="ano-esse"),
        pytest.param("ano passado", "01-01-2025", "31-12-2025", id="ano-passado"),
        pytest.param("proximo ano", "01-01-2027", "31-12-2027", id="ano-proximo"),
        pytest.param("ano que vem", "01-01-2027", "31-12-2027", id="ano-que-vem"),
    ],
)
def test_year_variations_resolve_date_range(phrase: str, start_date: str, end_date: str):
    resolved = ChatDateRangeIntentService.resolve(f"receita do {phrase}", today=_REFERENCE)

    assert resolved is not None
    assert resolved.start_date == start_date
    assert resolved.end_date == end_date


@pytest.mark.parametrize(
    "message",
    [
        "status fabril do produto 90269002 proximo trimestre",
        "status fabril do produto 90269002 esse semestre",
        "status fabril do produto 90269002 proximo ano",
        "status fabril do produto 90269002 ontem mesmo",
        "status fabril do produto 90269002 semana antepassada",
    ],
)
def test_factory_playbook_does_not_request_missing_date_for_new_variations(message: str):
    assert ChatOperationalParameterService.resolve_missing_date_answer(message) is None


@pytest.mark.parametrize(
    "phrase",
    [
        "proximo trimestre",
        "esse semestre",
        "semestre passado",
        "proximo ano",
        "semana antepassada",
        "hoje mesmo",
        "primeiro semestre",
    ],
)
def test_has_temporal_reference_for_expanded_vocabulary(phrase: str):
    message = f"status fabril do produto 90269002 {phrase}"

    assert ChatTemporalIntentService.has_temporal_reference(message)
    assert ChatOperationalDateParameterService.has_temporal_reference(message)
