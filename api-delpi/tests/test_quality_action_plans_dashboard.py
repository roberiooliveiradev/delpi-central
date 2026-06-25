from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


def test_dashboard_summary_with_branch_passes_single_sql_param():
  repo = PostgresQualityActionPlanRepository(connection=MagicMock())
  repo.fetch_one = MagicMock(
    side_effect=[
      {
        "open_plans": 1,
        "critical_open": 0,
        "waiting_validation": 0,
        "completed_this_month": 0,
      },
      {"overdue_actions": 0},
      {"overdue_plans": 0},
      {
        "avg_closure_days": None,
        "closure_sample_size": 0,
        "avg_time_to_effectiveness_days": None,
        "effectiveness_sample_size": 0,
      },
    ]
  )

  result = repo.get_dashboard_summary(branch_code="01")

  assert result["branch_code"] == "01"
  assert result["open_plans"] == 1
  assert "timing" in result
  main_query = repo.fetch_one.call_args_list[0][0][0]
  assert main_query.count("%s") == 1
  assert repo.fetch_one.call_args_list[0][0][1] == ("01",)


def test_dashboard_timing_kpis_rounds_days():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(
        return_value={
            "avg_closure_days": 14.567,
            "closure_sample_size": 5,
            "avg_time_to_effectiveness_days": 21.234,
            "effectiveness_sample_size": 4,
        }
    )

    timing = repo._fetch_timing_kpis(months=12)

    assert timing["window_months"] == 12
    assert timing["avg_closure_days"] == 14.6
    assert timing["closure_sample_size"] == 5
    assert timing["avg_time_to_effectiveness_days"] == 21.2
    assert timing["effectiveness_sample_size"] == 4
