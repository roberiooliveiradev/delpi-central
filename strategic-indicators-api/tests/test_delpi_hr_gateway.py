from __future__ import annotations

from unittest.mock import MagicMock

from si_app.infrastructure.gateways.delpi_hr_gateway import DelpiHrGateway


def test_hr_gateway_caches_snapshot_request() -> None:
    client = MagicMock()
    client.get_hr_snapshot.return_value = {
        "start_date": "01-04-2026",
        "end_date": "30-04-2026",
        "internal_satisfaction_pct": 74.0,
        "active_pdi_count": 12.0,
        "performance_reviews_completion_pct": 90.0,
        "branches": [
            {
                "branch_code": "01",
                "absenteeism_pct": 2.5,
                "turnover_pct": 4.0,
                "training_hours_per_collaborator": 2.0,
                "active_pdi_count": 7.0,
                "performance_reviews_completion_pct": 91.0,
            }
        ],
    }

    gateway = DelpiHrGateway(client)

    first = gateway.get_snapshot(
        branch="01",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    second = gateway.get_snapshot(
        branch="01",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )

    client.get_hr_snapshot.assert_called_once()
    assert first.internal_satisfaction_pct == 74.0
    assert first.branches[0].branch_code == "01"
    assert second is first
