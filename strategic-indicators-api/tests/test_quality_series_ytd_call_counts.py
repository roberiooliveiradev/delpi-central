"""E5.S3 — contagem GET quality no path série YTD (pós otimizações)."""

from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.quality.quality_metrics_snapshot_service import (
    QualityMetricsSnapshotService,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)

YTD_MONTHS = 6


def _ppm_series(*, competences: list[str], ppm: float = 1.0) -> dict:
    return {
        "points": [
            {
                "sort_key": competence,
                "ppm": ppm,
            }
            for competence in competences
        ]
    }


def _metric_series(
    *,
    competences: list[str],
    metrics: dict,
) -> dict:
    return {
        "points": [
            {
                "sort_key": competence,
                "metrics": metrics,
            }
            for competence in competences
        ]
    }


def _counting_gateway() -> tuple[MagicMock, list[str]]:
    calls: list[str] = []
    gateway = MagicMock()
    competences = [f"2026-{str(m).zfill(2)}" for m in range(1, YTD_MONTHS + 1)]

    def track(name: str, payload):
        def _inner(*args, **kwargs):
            calls.append(name)
            return payload

        return _inner

    gateway.list_branches.side_effect = track("list_branches", ["01", "02"])
    gateway.get_ppm_series.side_effect = track(
        "get_ppm_series",
        _ppm_series(competences=competences),
    )
    gateway.get_scrap_cost_pct_series.side_effect = track(
        "get_scrap_cost_pct_series",
        _metric_series(
            competences=competences,
            metrics={"scrap_cost_pct": 0.1},
        ),
    )
    gateway.get_rework_cost_pct_series.side_effect = track(
        "get_rework_cost_pct_series",
        _metric_series(
            competences=competences,
            metrics={"rework_cost_pct": 0.2},
        ),
    )
    gateway.get_kaizen_summary_series.side_effect = track(
        "get_kaizen_summary_series",
        _metric_series(
            competences=competences,
            metrics={"total_kaizens": 0, "total_savings": 0},
        ),
    )
    gateway.get_audit_5s_summary_series.side_effect = track(
        "get_audit_5s_summary_series",
        _metric_series(
            competences=competences,
            metrics={"average_score": 8.0},
        ),
    )
    return gateway, calls


def test_ytd_series_uses_series_endpoints_not_n_summaries() -> None:
    gateway, calls = _counting_gateway()
    service = QualityMetricsSnapshotService(quality_gateway=gateway)
    periods = [
        ResolvedPeriod(
            competence=f"2026-{str(m).zfill(2)}",
            start_date=f"01-{str(m).zfill(2)}-2026",
            end_date=f"28-{str(m).zfill(2)}-2026",
        )
        for m in range(1, YTD_MONTHS + 1)
    ]
    service.get_snapshot_series(periods=periods, branch=None)

    # PPM: 2 types × 3 prefixes × (None+01+02) = 18 (fixo na janela)
    assert calls.count("get_ppm_series") == 18
    # cost: scrap+rework × (None+01+02) = 6
    assert calls.count("get_scrap_cost_pct_series") == 3
    assert calls.count("get_rework_cost_pct_series") == 3
    # kaizen/5s: só filiais (sem bloco None) = 2 cada
    assert calls.count("get_kaizen_summary_series") == 2
    assert calls.count("get_audit_5s_summary_series") == 2

    assert gateway.get_ppm_summary.call_count == 0
    assert gateway.get_scrap_cost_pct.call_count == 0
    assert gateway.get_rework_cost_pct.call_count == 0
    assert gateway.get_kaizen_summary.call_count == 0
    assert gateway.get_audit_5s_summary.call_count == 0

    # Total: 2×list_branches + 18 PPM + 6 cost + 4 kaizen/5s = 30
    assert len(calls) == 30
