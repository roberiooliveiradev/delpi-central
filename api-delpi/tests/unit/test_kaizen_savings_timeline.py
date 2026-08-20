from datetime import date

import pytest

from app.domain.services.kaizen import kaizen_savings_timeline as timeline
from app.domain.services.kaizen.kaizen_savings_calculator import (
    ANNUAL_BUSINESS_DAYS,
    amount_for_active_calendar_days,
    calculate_annual_savings,
)


def _rev(number, effective_from, effective_until, daily, annual=None, version_status=None):
    return {
        "revision_number": number,
        "effective_from": effective_from,
        "effective_until": effective_until,
        "daily_savings": daily,
        "annual_savings": annual,
        "version_status": version_status,
    }


def test_single_improvement_capped_at_one_year():
    # Melhoria única implantada em 2024-01-01, sem fim de vigência.
    # Em 2026, já passou o aniversário (2025-01-01): não conta mais.
    revisions = [_rev(1, "2024-01-01", None, 10.0)]
    total = timeline.period_savings(
        revisions,
        date(2025, 6, 1),
        date(2025, 12, 31),
        today=date(2026, 7, 1),
    )
    assert total == 0.0


def test_single_improvement_within_validity():
    # 101 dias corridos → dias úteis equivalentes × diária.
    revisions = [_rev(1, "2024-01-01", None, 10.0)]
    total = timeline.period_savings(
        revisions,
        date(2024, 1, 1),
        date(2024, 4, 10),  # 101 dias inclusivos
        today=date(2024, 12, 31),
    )
    assert total == amount_for_active_calendar_days(10.0, 101)


def test_new_improvement_renews_anniversary():
    # v1 implantada 2024-01-01 (fecha em 2024-07-01), v2 em 2024-07-01 (vigente).
    revisions = [
        _rev(2, "2024-07-01", None, 20.0),
        _rev(1, "2024-01-01", "2024-07-01", 10.0),
    ]
    # Período todo 2024: v1 conta jan-jun, v2 conta jul-dez.
    total = timeline.period_savings(
        revisions,
        date(2024, 1, 1),
        date(2024, 12, 31),
        today=date(2024, 12, 31),
    )
    # v1: 2024-01-01 a 2024-06-30 = 182 dias corridos
    # v2: 2024-07-01 a 2024-12-31 = 184 dias corridos
    expected = amount_for_active_calendar_days(10.0, 182) + amount_for_active_calendar_days(
        20.0, 184
    )
    assert total == pytest.approx(expected)


def test_current_active_savings_picks_latest_within_validity():
    revisions = [
        _rev(2, "2026-06-01", None, 20.0, 5000.0),
        _rev(1, "2024-01-01", "2026-06-01", 10.0, 2000.0),
    ]
    current = timeline.current_active_savings(revisions, today=date(2026, 7, 1))
    assert current["active"] is True
    assert current["revision_number"] == 2
    assert current["annual_savings"] == 5000.0


def test_current_active_savings_expired():
    revisions = [_rev(1, "2024-01-01", None, 10.0, 2000.0)]
    current = timeline.current_active_savings(revisions, today=date(2026, 7, 1))
    assert current["active"] is False
    assert current["daily_savings"] is None


def test_draft_version_never_counts_in_period():
    # v1 implantada (contabiliza) + v2 em andamento (rascunho — não conta).
    revisions = [
        _rev(2, "2024-06-01", None, 99.0, version_status="recebido"),
        _rev(1, "2024-01-01", None, 10.0, version_status="implantado"),
    ]
    total = timeline.period_savings(
        revisions,
        date(2024, 1, 1),
        date(2024, 1, 10),  # 10 dias corridos
        today=date(2024, 6, 30),
    )
    assert total == amount_for_active_calendar_days(10.0, 10)


def test_current_active_ignores_draft_even_if_recent():
    revisions = [
        _rev(2, "2026-06-25", None, 99.0, 30000.0, version_status="recebido"),
        _rev(1, "2026-01-01", None, 10.0, 2000.0, version_status="implantado"),
    ]
    current = timeline.current_active_savings(revisions, today=date(2026, 7, 1))
    assert current["active"] is True
    assert current["revision_number"] == 1
    assert current["annual_savings"] == 2000.0


def test_superseded_version_counts_in_past_window():
    # v1 substituída conta no período em que esteve vigente.
    revisions = [
        _rev(2, "2024-07-01", None, 20.0, version_status="implantado"),
        _rev(1, "2024-01-01", "2024-07-01", 10.0, version_status="substituido"),
    ]
    total = timeline.period_savings(
        revisions,
        date(2024, 1, 1),
        date(2024, 6, 30),  # janela só da v1
        today=date(2024, 12, 31),
    )
    assert total == amount_for_active_calendar_days(10.0, 182)


def test_period_savings_zero_for_future_range():
    revisions = [_rev(1, "2026-01-10", None, 10.0, version_status="implantado")]
    total = timeline.period_savings(
        revisions,
        date(2026, 8, 1),
        date(2026, 8, 31),
        today=date(2026, 7, 8),
    )
    assert total == 0.0


def test_period_savings_projects_future_when_requested():
    """Ficha do kaizen: intervalo futuro dentro da validade projeta diária × dias úteis."""
    revisions = [_rev(1, "2026-01-10", None, 10.0, version_status="implantado")]
    total = timeline.period_savings(
        revisions,
        date(2026, 8, 1),
        date(2026, 8, 31),
        today=date(2026, 7, 8),
        project_future=True,
    )
    assert total == amount_for_active_calendar_days(10.0, 31)


def test_period_savings_projection_still_capped_by_validity():
    revisions = [_rev(1, "2026-01-10", None, 10.0, version_status="implantado")]
    # Validade até 2027-01-09; intervalo pedido vai além.
    total = timeline.period_savings(
        revisions,
        date(2026, 12, 1),
        date(2027, 6, 1),
        today=date(2026, 7, 8),
        project_future=True,
    )
    # 2026-12-01 .. 2027-01-09 = 40 dias corridos
    assert total == amount_for_active_calendar_days(10.0, 40)


def test_full_validity_year_matches_annual_savings():
    """365 dias corridos de validade ≡ diária × 253 (economia/ano)."""
    assert ANNUAL_BUSINESS_DAYS == 253
    daily = 0.69
    revisions = [
        _rev(
            1,
            "2026-08-12",
            None,
            daily,
            calculate_annual_savings(daily),
            version_status="implantado",
        )
    ]
    # Válido até 2027-08-11 → 365 dias corridos.
    total = timeline.period_savings(
        revisions,
        date(2026, 8, 12),
        date(2027, 8, 11),
        today=date(2026, 8, 12),
        project_future=True,
    )
    assert total == calculate_annual_savings(daily)
