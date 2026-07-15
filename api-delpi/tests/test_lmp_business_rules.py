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
