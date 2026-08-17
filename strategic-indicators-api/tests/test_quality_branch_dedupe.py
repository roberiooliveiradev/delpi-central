"""E3.S2 — sem duplicar PPM consolidado quando branch é explícita."""

from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.quality.quality_metrics_snapshot_service import (
    QualityMetricsSnapshotService,
)


def test_explicit_branch_does_not_double_ppm_summary_calls() -> None:
    gateway = MagicMock()
    gateway.get_ppm_summary.return_value = {"ppm": 3.0}
    gateway.get_scrap_cost_pct.return_value = {"scrap_cost_pct": 0.1}
    gateway.get_rework_cost_pct.return_value = {"rework_cost_pct": 0.2}
    gateway.get_kaizen_summary.return_value = {
        "total_kaizens": 0,
        "total_savings": 0,
    }
    gateway.get_audit_5s_summary.return_value = {"average_score": 8.0}

    service = QualityMetricsSnapshotService(quality_gateway=gateway)
    snapshot = service.get_snapshot(
        start_date="01-06-2026",
        end_date="30-06-2026",
        branch="01",
    )

    # 6 PPM (3 prefixes × internal/external) — sem bloco consolidado duplicado
    assert gateway.get_ppm_summary.call_count == 6
    assert snapshot.ppm_internal_consolidated == 3.0
    assert snapshot.branches[0].ppm_internal == 3.0
