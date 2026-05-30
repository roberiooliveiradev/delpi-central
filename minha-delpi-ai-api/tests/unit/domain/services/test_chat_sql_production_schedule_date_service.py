from datetime import date

from app.domain.services.chat_sql_production_schedule_date_service import (
    ChatSqlProductionScheduleDateService,
)


def test_resolve_today_by_default():
    reference = date(2026, 5, 29)  # sexta-feira

    resolved = ChatSqlProductionScheduleDateService.resolve(
        "quais produtos serão produzidos?",
        today=reference,
    )

    assert resolved.label == "hoje"
    assert "CAST(GETDATE()" in resolved.sql_date_declaration


def test_resolve_tomorrow():
    reference = date(2026, 5, 29)

    resolved = ChatSqlProductionScheduleDateService.resolve(
        "o que vai ser produzido amanhã?",
        today=reference,
    )

    assert resolved.label == "amanhã"
    assert resolved.target_date == date(2026, 5, 30)
    assert resolved.sql_date_declaration == "DECLARE @DATA DATE = '2026-05-30';"


def test_resolve_yesterday_for_production():
    resolved = ChatSqlProductionScheduleDateService.resolve(
        "quais produtos serão produzidos ontem?",
        today=date(2026, 5, 29),
    )

    assert resolved.target_date == date(2026, 5, 28)
    assert resolved.label == "ontem"


def test_resolve_next_monday_from_friday():
    reference = date(2026, 5, 29)  # sexta

    resolved = ChatSqlProductionScheduleDateService.resolve(
        "quais produtos serão produzidos na segunda-feira?",
        today=reference,
    )

    assert resolved.target_date == date(2026, 6, 1)
    assert "segunda-feira" in resolved.label
    assert "01/06/2026" in resolved.label


def test_resolve_monday_on_monday_includes_today():
    reference = date(2026, 6, 1)  # segunda

    resolved = ChatSqlProductionScheduleDateService.resolve(
        "programação de produção de segunda",
        today=reference,
    )

    assert resolved.target_date == reference
    assert "segunda-feira" in resolved.label


def test_resolve_next_monday_skips_today():
    reference = date(2026, 6, 1)  # segunda

    resolved = ChatSqlProductionScheduleDateService.resolve(
        "quais produtos serão produzidos na próxima segunda?",
        today=reference,
    )

    assert resolved.target_date == date(2026, 6, 8)


def test_infer_from_sql_literal_date():
    sql = "DECLARE @FILIAL CHAR(2) = '01';\nDECLARE @DATA DATE = '2026-06-02';\nSELECT 1"

    resolved = ChatSqlProductionScheduleDateService.infer_from_sql(sql)

    assert resolved is not None
    assert resolved.target_date == date(2026, 6, 2)
    assert "terça-feira" in resolved.label
