from datetime import date

from app.domain.services.kaizen import kaizen_savings_timeline as timeline


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
    # 100 dias ativos dentro do primeiro ano.
    revisions = [_rev(1, "2024-01-01", None, 10.0)]
    total = timeline.period_savings(
        revisions,
        date(2024, 1, 1),
        date(2024, 4, 10),  # 101 dias inclusivos
        today=date(2024, 12, 31),
    )
    assert total == 1010.0


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
    # v1: 2024-01-01 a 2024-06-30 = 182 dias × 10 = 1820
    # v2: 2024-07-01 a 2024-12-31 = 184 dias × 20 = 3680
    assert total == 1820.0 + 3680.0


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
        _rev(2, "2024-06-01", None, 99.0, version_status="em_andamento"),
        _rev(1, "2024-01-01", None, 10.0, version_status="implantado"),
    ]
    total = timeline.period_savings(
        revisions,
        date(2024, 1, 1),
        date(2024, 1, 10),  # 10 dias
        today=date(2024, 6, 30),
    )
    assert total == 100.0  # só a v1 implantada


def test_current_active_ignores_draft_even_if_recent():
    revisions = [
        _rev(2, "2026-06-25", None, 99.0, 30000.0, version_status="em_andamento"),
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
    assert total == 182 * 10.0
