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
      {
        "groups_detected": 0,
        "plans_in_window": 0,
        "open_plans_in_recurrence": 0,
      },
    ]
  )
  repo.fetch_all = MagicMock(return_value=[])

  result = repo.get_dashboard_summary(branch_code="01")

  assert result["branch_code"] == "01"
  assert result["open_plans"] == 1
  assert "timing" in result
  assert "breakdowns" in result
  assert "rankings" in result
  assert "recurrence_alert" in result
  main_query = repo.fetch_one.call_args_list[0][0][0]
  assert main_query.count("%s") == 1
  assert repo.fetch_one.call_args_list[0][0][1] == ("01",)


def test_dashboard_rankings_maps_rows():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(
        side_effect=[
            [{"label": "Cliente A", "total": 4, "open_plans": 2}],
            [{"label": "90261805", "total": 3, "open_plans": 1}],
            [{"label": "user-01", "total": 5, "open_plans": 3}],
        ]
    )

    rankings = repo._fetch_rankings(months=12, limit=8)

    assert rankings["window_months"] == 12
    assert rankings["by_customer"][0]["open_plans"] == 2
    assert rankings["by_product"][0]["label"] == "90261805"
    assert rankings["by_owner"][0]["total"] == 5


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


def test_dashboard_breakdowns_maps_rows():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_all = MagicMock(
        side_effect=[
            [{"label": "Método", "total": 3}],
            [{"label": "oxidacao", "total": 2}],
            [{"label": "corrective", "total": 5}],
        ]
    )

    breakdowns = repo._fetch_breakdowns(months=6, limit=8)

    assert breakdowns["window_months"] == 6
    assert breakdowns["by_root_cause"][0]["label"] == "Método"
    assert breakdowns["by_failure_mode"][0]["total"] == 2
    assert breakdowns["by_action_type"][0]["label"] == "corrective"


def test_dashboard_recurrence_alert_maps_rows():
    repo = PostgresQualityActionPlanRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(
        return_value={
            "groups_detected": 2,
            "plans_in_window": 5,
            "open_plans_in_recurrence": 3,
        }
    )
    repo.fetch_all = MagicMock(
        return_value=[
            {
                "recurrence_key": "90261805|oxidacao",
                "plans_in_window": 3,
                "total_plans": 4,
                "open_plans": 2,
                "product_code": "90261805",
                "failure_mode": "oxidacao",
                "branch_code": "01",
            }
        ]
    )

    alert = repo._fetch_recurrence_alert(months=12, limit=5)

    assert alert["window_months"] == 12
    assert alert["groups_detected"] == 2
    assert alert["plans_in_window"] == 5
    assert alert["open_plans_in_recurrence"] == 3
    assert alert["top_groups"][0]["product_code"] == "90261805"
    assert alert["top_groups"][0]["plans_in_window"] == 3
