from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys


def _body(response) -> dict:
    return json.loads(response.body.decode())


def _transforma_mais_goal() -> dict:
    return {
        "source_key": goal_keys.ENGINEERING_TRANSFORMA_MAIS,
        "goal_label": "R$ 12.000,00",
        "comparable_goal": 12000.0,
        "has_goal": True,
        "goal_scope_branch": "",
        "goal_scope_label": "Meta consolidada",
        "performance_direction": "higher_is_better",
        "value_prefix": "R$",
        "value_decimals": 2,
    }


@patch(
    "app.interface.http.routes.engineering.engineering_router.enrich_dashboard_metric",
    wraps=None,
)
@patch(
    "app.interface.http.routes.engineering.engineering_router.build_engineering_get_transforma_mais_summary_use_case"
)
def test_get_transforma_mais_summary_enriches_si_goal_with_filial_all(
    mock_build_use_case: MagicMock,
    mock_enrich: MagicMock,
) -> None:
    """TV manda filial_id=all; enrich deve ainda anexar comparable_goal (Meta)."""
    from app.interface.http.routes.engineering.engineering_router import get_process_summary

    mock_build_use_case.return_value.execute.return_value.to_dict.return_value = {
        "implemented_solutions_count": 40,
        "solutions_started_in_period_count": 0,
        "total_net_savings_until_now": 8000.0,
        "total_hours_saved_until_now": 235.95,
        "total_gross_costs_until_now": 1000.0,
        "total_investment_in_period": 1000.0,
        "total_gross_savings_in_period": 8866.35,
        "average_roi": 1.2,
        "monthly_breakdown": [],
    }

    def enrich_side_effect(payload, **kwargs):
        assert kwargs.get("source_key") == goal_keys.ENGINEERING_TRANSFORMA_MAIS
        # Router ainda passa filial_id bruto; normalize_si_branch no service
        # converte all → None. Aqui só garantimos que o enrich é chamado e anexa Meta.
        return {**payload, **_transforma_mais_goal()}

    mock_enrich.side_effect = enrich_side_effect

    response = get_process_summary(filial_id="all")

    assert response.status_code == 200
    data = _body(response)["data"]
    assert data["comparable_goal"] == 12000.0
    assert data["total_gross_savings_in_period"] == 8866.35
    mock_enrich.assert_called_once()
    assert mock_enrich.call_args.kwargs["branch"] == "all"


def test_dashboard_goals_service_all_branch_loads_consolidated_goal() -> None:
    """normalize_si_branch(all) → None antes do fetch SI — Meta consolidada volta."""
    from app.application.services.strategic_indicators.dashboard_goals_service import (
        DashboardGoalsService,
    )

    service = DashboardGoalsService()
    with patch.object(service, "_load_goals_map", return_value={
        goal_keys.ENGINEERING_TRANSFORMA_MAIS: _transforma_mais_goal(),
    }) as mock_load:
        goal = service.get_goal(
            source_key=goal_keys.ENGINEERING_TRANSFORMA_MAIS,
            branch="all",
        )

    assert goal is not None
    assert goal["comparable_goal"] == 12000.0
    assert mock_load.call_args.kwargs["branch"] is None
