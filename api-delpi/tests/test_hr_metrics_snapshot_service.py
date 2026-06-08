from unittest.mock import MagicMock

from app.application.services.hr.hr_metrics_snapshot_service import HrMetricsSnapshotService


def _mock_repository(*, pdi_by_branch: dict[str, dict]) -> MagicMock:
    repository = MagicMock()
    repository.list_active_branches.return_value = list(pdi_by_branch.keys())
    repository.get_absenteeism_snapshot.return_value = {
        "total_absence_hours": 0,
        "expected_hours": 0,
    }
    repository.get_turnover_snapshot.return_value = {
        "terminations_count": 0,
        "active_count": 0,
    }
    repository.get_training_hours_snapshot.return_value = {
        "total_training_hours": 0,
        "total_participations": 0,
    }
    repository.get_performance_reviews_completion_snapshot.return_value = {"value": 90}
    repository.get_internal_satisfaction_snapshot.return_value = {"value": 68.89}
    repository.get_active_pdi_snapshot.side_effect = (
        lambda *, branch_code, start_date, end_date: pdi_by_branch[branch_code]
    )
    return repository


def test_consolidated_active_pdi_count_sums_latest_branch_values():
    repository = _mock_repository(
        pdi_by_branch={
            "01": {
                "active_pdis": 15,
                "total_pdis": 20,
                "active_pdi_pct": 75.0,
            },
            "02": {
                "active_pdis": 8,
                "total_pdis": 10,
                "active_pdi_pct": 80.0,
            },
        }
    )

    snapshot = HrMetricsSnapshotService(repository=repository).get_snapshot(
        start_date=None,
        end_date=None,
        branch=None,
    )

    assert snapshot.active_pdi_count == 23
    assert snapshot.active_pdi_pct == 77.5


def test_active_pdi_pct_passes_through_repository_value_without_cap():
    repository = _mock_repository(
        pdi_by_branch={
            "01": {
                "active_pdis": 34,
                "total_pdis": 25,
                "active_pdi_pct": 136.0,
            },
        }
    )

    snapshot = HrMetricsSnapshotService(repository=repository).get_snapshot(
        start_date=None,
        end_date=None,
        branch="01",
    )

    assert snapshot.branches[0].active_pdi_count == 34
    assert snapshot.branches[0].active_pdi_pct == 136.0
