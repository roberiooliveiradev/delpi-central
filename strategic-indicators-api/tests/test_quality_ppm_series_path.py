"""E3.S1 — PPM via series no path multi-mês."""

from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.quality.quality_metrics_snapshot_service import (
    QualityMetricsSnapshotService,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)


def _series_payload(*, competences: list[str], ppm: float = 5.0) -> dict:
    return {
        "points": [
            {
                "sort_key": competence,
                "start_date": f"01-{competence[5:]}-{competence[:4]}",
                "end_date": f"28-{competence[5:]}-{competence[:4]}",
                "ppm": ppm,
            }
            for competence in competences
        ]
    }


def test_snapshot_series_uses_ppm_series_not_n_summaries() -> None:
    gateway = MagicMock()
    gateway.list_branches.return_value = ["01", "02"]
    gateway.get_ppm_series.return_value = _series_payload(
        competences=["2026-01", "2026-02"],
        ppm=7.5,
    )
    gateway.get_scrap_cost_pct_series.return_value = {
        "points": [
            {"sort_key": c, "metrics": {"scrap_cost_pct": 0.1}}
            for c in ("2026-01", "2026-02")
        ]
    }
    gateway.get_rework_cost_pct_series.return_value = {
        "points": [
            {"sort_key": c, "metrics": {"rework_cost_pct": 0.2}}
            for c in ("2026-01", "2026-02")
        ]
    }
    gateway.get_kaizen_summary_series.return_value = {
        "points": [
            {
                "sort_key": c,
                "metrics": {"total_kaizens": 0, "total_savings": 0},
            }
            for c in ("2026-01", "2026-02")
        ]
    }
    gateway.get_audit_5s_summary_series.return_value = {
        "points": [
            {"sort_key": c, "metrics": {"average_score": 8.0}}
            for c in ("2026-01", "2026-02")
        ]
    }

    service = QualityMetricsSnapshotService(quality_gateway=gateway)
    periods = [
        ResolvedPeriod(
            competence="2026-01",
            start_date="01-01-2026",
            end_date="31-01-2026",
        ),
        ResolvedPeriod(
            competence="2026-02",
            start_date="01-02-2026",
            end_date="28-02-2026",
        ),
    ]
    result = service.get_snapshot_series(periods=periods, branch=None)

    assert gateway.get_ppm_summary.call_count == 0
    assert gateway.get_kaizen_summary.call_count == 0
    assert gateway.get_audit_5s_summary.call_count == 0
    # 2 types × 3 prefixes × (consolidated + 01 + 02) = 18
    assert gateway.get_ppm_series.call_count == 18
    assert len(result) == 2
    assert result["2026-01"].ppm_internal_consolidated == 7.5
    assert result["2026-02"].ppm_internal_consolidated == 7.5
