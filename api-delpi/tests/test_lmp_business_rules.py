"""Regressão: LMP aberta não é Atrasado; Pontual/Atrasado só no fechamento."""

from datetime import date

from app.application.services.lmp_business_rules import LMPBusinessRules


def test_open_lmp_stays_in_progress_even_when_sla_would_have_been_exceeded() -> None:
    """LMP ABERTA acima do SLA permanece Andamento — atraso só no fechamento."""
    status = LMPBusinessRules.resolve_dashboard_status(
        start_date_str="20260101",
        end_date_str=None,
        qtd_pi=5,  # Nível 1 → SLA curto
        engineering_status="ABERTA",
        engineering_total_minutes=LMPBusinessRules.get_sla_limit_minutes("Nível 1") + 10_000,
        today=date(2026, 7, 15),
    )
    assert status == LMPBusinessRules.DASHBOARD_STATUS_IN_PROGRESS


def test_partial_lmp_stays_in_progress() -> None:
    status = LMPBusinessRules.resolve_dashboard_status(
        start_date_str="20260101",
        end_date_str="20260120",
        qtd_pi=5,
        engineering_status="PARCIAL",
        engineering_total_minutes=99_999,
        today=date(2026, 7, 15),
    )
    assert status == LMPBusinessRules.DASHBOARD_STATUS_IN_PROGRESS


def test_finished_lmp_can_be_late() -> None:
    status = LMPBusinessRules.resolve_dashboard_status(
        start_date_str="20260101",
        end_date_str="20260301",
        qtd_pi=5,
        engineering_status="FINALIZADA",
        engineering_total_minutes=LMPBusinessRules.get_sla_limit_minutes("Nível 1") + 1,
        today=date(2026, 7, 15),
    )
    assert status == LMPBusinessRules.DASHBOARD_STATUS_LATE


def test_finished_lmp_can_be_on_time_by_minutes() -> None:
    status = LMPBusinessRules.resolve_dashboard_status(
        start_date_str="20260101",
        end_date_str="20260301",
        qtd_pi=5,
        engineering_status="FINALIZADA",
        engineering_total_minutes=60,
        today=date(2026, 7, 15),
    )
    assert status == LMPBusinessRules.DASHBOARD_STATUS_ON_TIME


def test_returned_lmp_is_returned() -> None:
    status = LMPBusinessRules.resolve_dashboard_status(
        start_date_str="20260101",
        end_date_str=None,
        qtd_pi=5,
        engineering_status="RETORNADA",
        engineering_total_minutes=99_999,
        today=date(2026, 7, 15),
    )
    assert status == LMPBusinessRules.DASHBOARD_STATUS_RETURNED


def test_format_date_for_response_converts_yyyymmdd_to_br() -> None:
    assert LMPBusinessRules.format_date_for_response("20260723") == "23/07/2026"
    assert LMPBusinessRules.format_date_for_response("23/07/2026") == "23/07/2026"
    assert LMPBusinessRules.format_date_for_response("") is None
    assert LMPBusinessRules.format_date_for_response(None) is None
    assert LMPBusinessRules.format_date_for_response("        ") is None


def test_parse_totvs_date_accepts_br_and_ymd() -> None:
    assert LMPBusinessRules.parse_totvs_date("20260723") == date(2026, 7, 23)
    assert LMPBusinessRules.parse_totvs_date("23/07/2026") == date(2026, 7, 23)


def test_format_payload_dates_formats_known_keys() -> None:
    payload = LMPBusinessRules.format_payload_dates(
        {
            "start_date": "20260720",
            "end_date": "20260723",
            "sale_number": "003578",
            "status": "1",
        }
    )
    assert payload["start_date"] == "20/07/2026"
    assert payload["end_date"] == "23/07/2026"
    assert payload["sale_number"] == "003578"
