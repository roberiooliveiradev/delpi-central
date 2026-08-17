"""Baseline E1.S4 — contagem esperada de chamadas HTTP por mês (código atual)."""

from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.quality.quality_metrics_snapshot_service import (
    QualityMetricsSnapshotService,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.application.services.supplies.supplies_metrics_snapshot_service import (
    SuppliesMetricsSnapshotService,
)

# Contagens travadas em E1.S4 (antes de E2/E3). Atualizar em E5.S3 após otimizações.
BASELINE_QUALITY_GATEWAY_CALLS_PER_MONTH_CONSOLIDATED = 32
BASELINE_SUPPLIES_CORE_FETCHES_PER_MONTH = 4  # cpv, rol, stock, otd (sem negotiation)
BASELINE_YTD_MONTHS_EXAMPLE = 6


def _counting_quality_gateway() -> tuple[MagicMock, list[str]]:
    calls: list[str] = []
    gateway = MagicMock()

    def track(name: str):
        def _inner(*args, **kwargs):
            calls.append(name)
            if name == "list_branches":
                return ["01", "02"]
            if name == "get_ppm_series":
                return {
                    "points": [
                        {
                            "sort_key": f"2026-{str(m).zfill(2)}",
                            "ppm": 1.0,
                        }
                        for m in range(1, 13)
                    ]
                }
            if "ppm" in name:
                return {"ppm": 1.0}
            if "cost" in name:
                return {"percentage": 1.0}
            if "kaizen" in name:
                return {"total_kaizens": 0, "total_savings": 0, "list_kaizen": []}
            if "audit" in name:
                return {"average_score": 1.0, "list_audits": []}
            return {}

        return _inner

    gateway.list_branches.side_effect = track("list_branches")
    gateway.get_ppm_summary.side_effect = track("get_ppm_summary")
    gateway.get_ppm_series.side_effect = track("get_ppm_series")
    gateway.get_scrap_cost_pct.side_effect = track("get_scrap_cost_pct")
    gateway.get_rework_cost_pct.side_effect = track("get_rework_cost_pct")
    gateway.get_kaizen_summary.side_effect = track("get_kaizen_summary")
    gateway.get_audit_5s_summary.side_effect = track("get_audit_5s_summary")
    return gateway, calls


def test_baseline_quality_calls_per_month_consolidated() -> None:
    gateway, calls = _counting_quality_gateway()
    service = QualityMetricsSnapshotService(quality_gateway=gateway)
    service.get_snapshot(
        start_date="01-06-2026",
        end_date="30-06-2026",
        branch=None,
    )
    assert len(calls) == BASELINE_QUALITY_GATEWAY_CALLS_PER_MONTH_CONSOLIDATED
    assert "get_ppm_series" not in calls


def test_baseline_quality_series_uses_ppm_series_once_per_scope() -> None:
    """Após E3.S1: PPM não escala ×meses; series = 18 calls fixas na janela."""
    gateway, calls = _counting_quality_gateway()
    service = QualityMetricsSnapshotService(quality_gateway=gateway)
    periods = [
        ResolvedPeriod(
            competence=f"2026-{str(m).zfill(2)}",
            start_date=f"01-{str(m).zfill(2)}-2026",
            end_date=f"28-{str(m).zfill(2)}-2026",
        )
        for m in range(1, BASELINE_YTD_MONTHS_EXAMPLE + 1)
    ]
    service.get_snapshot_series(periods=periods, branch=None)
    assert calls.count("get_ppm_series") == 18
    assert calls.count("get_ppm_summary") == 0


def test_baseline_supplies_core_fetches_per_month() -> None:
    supplies = MagicMock()
    financial = MagicMock()
    supplies.fetch_cpv_raw.return_value = {}
    supplies.fetch_stock_value_raw.return_value = {}
    supplies.fetch_otd_raw.return_value = {}
    supplies.fetch_negotiation_savings_summary.return_value = {"branches": []}
    financial.get_rol.return_value = {}

    service = SuppliesMetricsSnapshotService(
        supplies_gateway=supplies,
        financial_gateway=financial,
    )
    service.get_snapshot(
        start_date="01-06-2026",
        end_date="30-06-2026",
        branch=None,
    )

    core = (
        supplies.fetch_cpv_raw.call_count
        + financial.get_rol.call_count
        + supplies.fetch_stock_value_raw.call_count
        + supplies.fetch_otd_raw.call_count
    )
    assert core == BASELINE_SUPPLIES_CORE_FETCHES_PER_MONTH
