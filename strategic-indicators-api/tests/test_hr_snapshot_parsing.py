from __future__ import annotations

from delpi_domain.hr_snapshot import parse_hr_snapshot_payload
from si_app.infrastructure.providers.strategic_indicators.hr_indicators_snapshot_provider import (
    HrIndicatorsSnapshotProvider,
)


def test_parse_hr_snapshot_payload_maps_api_response() -> None:
    snapshot = parse_hr_snapshot_payload(
        {
            "start_date": "01-05-2026",
            "end_date": "31-05-2026",
            "internal_satisfaction_pct": 80.5,
            "active_pdi_count": 23.0,
            "performance_reviews_completion_pct": 94.92,
            "branches": [
                {
                    "branch_code": "01",
                    "absenteeism_pct": 2.1,
                    "turnover_pct": 3.5,
                    "training_hours_per_collaborator": 1.8,
                    "active_pdi_count": 15.0,
                    "performance_reviews_completion_pct": 95.0,
                },
                {
                    "branch_code": "02",
                    "absenteeism_pct": 1.9,
                    "turnover_pct": 4.2,
                    "training_hours_per_collaborator": 2.1,
                    "active_pdi_count": 8.0,
                    "performance_reviews_completion_pct": 94.5,
                },
            ],
        }
    )

    assert snapshot.start_date == "01-05-2026"
    assert snapshot.internal_satisfaction_pct == 80.5
    assert len(snapshot.branches) == 2
    assert snapshot.branches[0].absenteeism_pct == 2.1


def test_provider_maps_global_satisfaction_to_branch_unit_values() -> None:
    from unittest.mock import MagicMock

    from delpi_domain.hr_snapshot import HrBranchSnapshot, HrMetricsSnapshot

    service = MagicMock()
    service.get_snapshot.return_value = HrMetricsSnapshot(
        start_date="01-04-2026",
        end_date="30-04-2026",
        branches=[
            HrBranchSnapshot(
                branch_code="01",
                absenteeism_pct=None,
                turnover_pct=None,
                training_hours_per_collaborator=None,
            ),
            HrBranchSnapshot(
                branch_code="02",
                absenteeism_pct=None,
                turnover_pct=None,
                training_hours_per_collaborator=None,
            ),
        ],
        internal_satisfaction_pct=73.54,
    )

    provider = HrIndicatorsSnapshotProvider(hr_metrics_snapshot_service=service)
    result = provider.get_hr_indicators_snapshot(
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    satisfaction = next(
        item for item in result["items"] if item["indicator_id"] == "hr-satisfaction"
    )

    assert satisfaction["unit_values"] == {"01": 73.54, "02": 73.54}
    assert satisfaction["value"] == 73.54
