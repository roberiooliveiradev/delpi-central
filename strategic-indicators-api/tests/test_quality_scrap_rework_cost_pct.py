from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.quality.quality_metrics_snapshot_service import (
    QualityBranchSnapshot,
    QualityMetricsSnapshot,
    QualityMetricsSnapshotService,
)
from si_app.infrastructure.gateways.delpi_quality_gateway import DelpiQualityGateway
from si_app.infrastructure.providers.strategic_indicators.quality_indicators_snapshot_provider import (
    QualityIndicatorsSnapshotProvider,
)


def test_scrap_and_rework_gateway_cache() -> None:
    client = MagicMock()
    client.get_quality_scrap_cost_pct.return_value = {"scrap_cost_pct": 0.6}
    client.get_quality_rework_cost_pct.return_value = {"rework_cost_pct": 0.1}

    gateway = DelpiQualityGateway(client)
    first = gateway.get_scrap_cost_pct(
        branch="01", date_start="2026-06-01", date_end="2026-06-30"
    )
    second = gateway.get_scrap_cost_pct(
        branch="01", date_start="2026-06-01", date_end="2026-06-30"
    )
    rework = gateway.get_rework_cost_pct(
        branch=None, date_start="2026-06-01", date_end="2026-06-30"
    )

    assert first["scrap_cost_pct"] == 0.6
    assert second["scrap_cost_pct"] == 0.6
    assert rework["rework_cost_pct"] == 0.1
    client.get_quality_scrap_cost_pct.assert_called_once()
    client.get_quality_rework_cost_pct.assert_called_once()


def test_quality_provider_emits_scrap_and_rework_cost_pct() -> None:
    snapshot = QualityMetricsSnapshot(
        start_date="2026-06-01",
        end_date="2026-06-30",
        branches=[
            QualityBranchSnapshot(
                branch="01",
                ppm_internal=100.0,
                ppm_external=50.0,
                kaizen_ideas_avg=1.0,
                kaizen_financial_gain=10.0,
                audit_5s_score=80.0,
                scrap_cost_pct=0.55,
                rework_cost_pct=0.08,
            ),
            QualityBranchSnapshot(
                branch="02",
                ppm_internal=120.0,
                ppm_external=40.0,
                kaizen_ideas_avg=2.0,
                kaizen_financial_gain=20.0,
                audit_5s_score=85.0,
                scrap_cost_pct=0.7,
                rework_cost_pct=0.12,
            ),
        ],
        scrap_cost_pct_consolidated=0.62,
        rework_cost_pct_consolidated=0.1,
    )
    service = MagicMock(spec=QualityMetricsSnapshotService)
    service.get_snapshot.return_value = snapshot

    provider = QualityIndicatorsSnapshotProvider(
        quality_metrics_snapshot_service=service
    )
    result = provider.get_quality_indicators_snapshot(
        start_date="2026-06-01",
        end_date="2026-06-30",
        branch=None,
    )

    by_id = {item["indicator_id"]: item for item in result["items"]}
    scrap = by_id["quality-scrap-cost-pct"]
    rework = by_id["quality-rework-cost-pct"]

    assert scrap["source"] == "quality_scrap_cost_pct"
    assert scrap["value"] == 0.62
    assert scrap["unit_values"] == {"01": 0.55, "02": 0.7}
    assert rework["source"] == "quality_rework_cost_pct"
    assert rework["value"] == 0.1
    assert rework["unit_values"] == {"01": 0.08, "02": 0.12}


def test_quality_snapshot_resolves_cost_pct_fields() -> None:
    gateway = MagicMock()
    gateway.list_branches.return_value = ["01"]
    gateway.get_ppm_summary.return_value = {"ppm": 10.0}
    gateway.get_kaizen_summary.return_value = {
        "total_kaizens": 0,
        "total_savings": 0,
        "list_kaizen": [],
    }
    gateway.get_audit_5s_summary.return_value = {"average_score": 0, "list_audits": []}
    gateway.get_scrap_cost_pct.side_effect = [
        {"scrap_cost_pct": 0.5},  # consolidated (branch=None)
        {"scrap_cost_pct": 0.55},  # branch 01
    ]
    gateway.get_rework_cost_pct.side_effect = [
        {"rework_cost_pct": 0.09},
        {"rework_cost_pct": 0.08},
    ]

    service = QualityMetricsSnapshotService(quality_gateway=gateway)
    snapshot = service.get_snapshot(
        start_date="2026-06-01",
        end_date="2026-06-30",
        branch=None,
    )

    assert snapshot.scrap_cost_pct_consolidated == 0.5
    assert snapshot.rework_cost_pct_consolidated == 0.09
    assert snapshot.branches[0].scrap_cost_pct == 0.55
    assert snapshot.branches[0].rework_cost_pct == 0.08
