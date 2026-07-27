from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys


def _body(response) -> dict:
    return json.loads(response.body.decode())


def _financial_goal() -> dict:
    return {
        "source_key": goal_keys.QUALITY_KAIZEN_FINANCIAL,
        "goal_label": "R$ 4.500,00/mês",
        "comparable_goal": 4500.0,
        "has_goal": True,
        "goal_scope_branch": "01",
        "goal_scope_label": "Meta filial 01",
        "performance_direction": "higher_is_better",
        "value_prefix": "R$",
        "value_suffix": "/mês",
        "value_decimals": 2,
    }


def _ideas_goal() -> dict:
    return {
        "source_key": goal_keys.QUALITY_KAIZEN_IDEAS,
        "goal_label": "8,00 ideias/mês",
        "comparable_goal": 8.0,
        "has_goal": True,
        "goal_scope_branch": "01",
        "goal_scope_label": "Meta filial 01",
        "performance_direction": "higher_is_better",
        "value_suffix": " ideias/mês",
        "value_decimals": 2,
    }


@patch("app.interface.http.routes.quality.quality_router.enrich_dashboard_metric")
@patch("app.interface.http.routes.quality.quality_router.build_get_kaizen_summary_use_case")
def test_get_kaizen_summary_enriches_financial_and_ideas_goals(
    mock_build_use_case: MagicMock,
    mock_enrich: MagicMock,
) -> None:
    from app.interface.http.routes.quality.quality_router import get_kaizen_summary

    mock_build_use_case.return_value.execute.return_value.to_dict.return_value = {
        "total_kaizens": 1,
        "total_savings": 1940.0,
        "list_kaizen": [],
    }

    def enrich_side_effect(payload, **kwargs):
        if kwargs.get("summary_key") == "ideas_goal":
            return {
                **payload,
                "ideas_goal": {
                    **payload["ideas_goal"],
                    **_ideas_goal(),
                },
            }
        if kwargs.get("source_key") == goal_keys.QUALITY_KAIZEN_FINANCIAL:
            return {**payload, **_financial_goal()}
        return payload

    mock_enrich.side_effect = enrich_side_effect

    response = get_kaizen_summary(branch="01")

    assert response.status_code == 200
    body = _body(response)
    data = body["data"]
    assert data["comparable_goal"] == 4500.0
    assert data["total_savings"] == 1940.0
    assert data["value"] == 1940.0
    assert data["ideas_goal"]["comparable_goal"] == 8.0
    assert data["ideas_goal"]["total_kaizens"] == 1
    assert data["ideas_goal"]["value"] == 1
    summary = data["summary"]
    assert summary["branch_filter_applied"] is True
    assert summary["consolidated_across_branches"] is False
    assert summary["is_complete"] is True
    assert summary["total_savings"] == 1940.0
    assert summary["total_kaizens"] == 1

    assert mock_enrich.call_count == 2
    first_call = mock_enrich.call_args_list[0].kwargs
    second_call = mock_enrich.call_args_list[1].kwargs
    assert first_call["source_key"] == goal_keys.QUALITY_KAIZEN_IDEAS
    assert first_call["summary_key"] == "ideas_goal"
    assert second_call["source_key"] == goal_keys.QUALITY_KAIZEN_FINANCIAL
