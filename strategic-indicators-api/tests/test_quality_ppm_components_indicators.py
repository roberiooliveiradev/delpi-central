from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.quality.quality_metrics_snapshot_service import (
    QualityBranchSnapshot,
    QualityMetricsSnapshot,
    QualityMetricsSnapshotService,
)
from si_app.infrastructure.providers.strategic_indicators.quality_indicators_snapshot_provider import (
    QualityIndicatorsSnapshotProvider,
)


def test_quality_provider_emits_ppm_components_indicators() -> None:
    snapshot = QualityMetricsSnapshot(
        start_date="2026-08-01",
        end_date="2026-08-31",
        branches=[
            QualityBranchSnapshot(
                branch="01",
                ppm_internal=100.0,
                ppm_external=50.0,
                kaizen_ideas_avg=1.0,
                kaizen_financial_gain=10.0,
                audit_5s_score=80.0,
                ppm_internal_components=210.0,
                ppm_external_components=80.0,
            ),
            QualityBranchSnapshot(
                branch="02",
                ppm_internal=120.0,
                ppm_external=40.0,
                kaizen_ideas_avg=2.0,
                kaizen_financial_gain=20.0,
                audit_5s_score=85.0,
                ppm_internal_components=190.0,
                ppm_external_components=70.0,
            ),
        ],
        ppm_internal_components_consolidated=200.0,
        ppm_external_components_consolidated=75.0,
    )
    service = MagicMock(spec=QualityMetricsSnapshotService)
    service.get_snapshot.return_value = snapshot

    provider = QualityIndicatorsSnapshotProvider(
        quality_metrics_snapshot_service=service
    )
    result = provider.get_quality_indicators_snapshot(
        start_date="2026-08-01",
        end_date="2026-08-31",
        branch=None,
    )

    by_id = {item["indicator_id"]: item for item in result["items"]}
    internal = by_id["quality-ppm-internal-components"]
    external = by_id["quality-ppm-external-components"]

    assert internal["source"] == "quality_ppm_internal_components"
    assert internal["value"] == 200.0
    assert internal["unit_values"] == {"01": 210.0, "02": 190.0}
    assert external["source"] == "quality_ppm_external_components"
    assert external["value"] == 75.0
    assert external["unit_values"] == {"01": 80.0, "02": 70.0}
