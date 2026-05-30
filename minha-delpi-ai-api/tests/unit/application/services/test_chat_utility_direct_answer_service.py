from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.application.services.chat_utility_direct_answer_service import (
    ChatUtilityDirectAnswerService,
)


@pytest.mark.parametrize(
    "message",
    [
        "que horas são?",
        "que horas sao",
        "qual a hora?",
        "que dia é hoje?",
        "qual a data?",
        "que dia da semana é hoje?",
        "data e hora",
        "qual o ano?",
        "que ano estamos",
    ],
)
def test_utility_question_detection(message: str):
    assert ChatUtilityDirectAnswerService.is_utility_question(message)
    assert ChatUtilityDirectAnswerService.classify(message)


@pytest.mark.parametrize(
    "message",
    [
        "estoque do produto 10080047",
        "qual a hora de inicio da ordem 123",
        "tempo real de producao em hora mil",
        "bom dia",
    ],
)
def test_non_utility_questions(message: str):
    assert not ChatUtilityDirectAnswerService.is_utility_question(message)


def test_current_time_answer_uses_configured_timezone():
    fixed = datetime(2026, 5, 30, 12, 8, tzinfo=ZoneInfo("America/Sao_Paulo"))
    answer = ChatUtilityDirectAnswerService.build_direct_answer(
        message="que horas são?",
        now=fixed,
    )

    assert answer
    assert "12:08" in answer
    assert "Brasília" in answer


def test_current_date_answer():
    fixed = datetime(2026, 5, 30, 12, 8, tzinfo=ZoneInfo("America/Sao_Paulo"))
    answer = ChatUtilityDirectAnswerService.build_direct_answer(
        message="que dia é hoje?",
        now=fixed,
    )

    assert answer
    assert "30/05/2026" in answer
    assert "sábado" in answer


def test_current_weekday_answer():
    fixed = datetime(2026, 5, 30, 12, 8, tzinfo=ZoneInfo("America/Sao_Paulo"))
    answer = ChatUtilityDirectAnswerService.build_direct_answer(
        message="que dia da semana é hoje?",
        now=fixed,
    )

    assert answer
    assert "sábado" in answer


def test_current_year_answer():
    fixed = datetime(2026, 5, 30, 12, 8, tzinfo=ZoneInfo("America/Sao_Paulo"))
    answer = ChatUtilityDirectAnswerService.build_direct_answer(
        message="qual o ano?",
        now=fixed,
    )

    assert answer
    assert "2026" in answer
