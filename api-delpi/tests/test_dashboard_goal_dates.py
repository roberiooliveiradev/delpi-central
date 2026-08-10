from app.application.services.strategic_indicators.dashboard_goal_dates import (
    normalize_si_branch,
    normalize_si_period_date,
)


def test_normalize_si_period_date_from_iso() -> None:
    assert normalize_si_period_date("2026-05-22") == "22-05-2026"


def test_normalize_si_period_date_keeps_delpi_format() -> None:
    assert normalize_si_period_date("22-05-2026") == "22-05-2026"


def test_normalize_si_branch_pads_totvs_code() -> None:
    assert normalize_si_branch("2") == "02"
    assert normalize_si_branch("") is None


def test_normalize_si_branch_all_aliases_mean_consolidated() -> None:
    """filial_id=all da TV não pode ir literal à SI (quebra Meta consolidada)."""
    assert normalize_si_branch("all") is None
    assert normalize_si_branch("ALL") is None
    assert normalize_si_branch("Todas") is None
    assert normalize_si_branch("todas") is None
    assert normalize_si_branch("todos") is None
    assert normalize_si_branch("01") == "01"
    assert normalize_si_branch("02") == "02"
