"""Smoke Nível A — séries quality scrap/rework/kaizen/5s (E3.S3)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_LOSSES = "app.interface.http.routes.quality.losses_routes"
_Q = "app.interface.http.routes.quality.quality_router"


@patch(f"{_LOSSES}.build_get_refugos_scrap_cost_pct_use_case")
def test_get_quality_scrap_cost_pct_series_returns_meta(mock_builder) -> None:
    from app.interface.http.routes.quality.losses_routes import (
        get_quality_scrap_cost_pct_series,
    )

    mock_builder.return_value = MagicMock(
        execute=MagicMock(return_value={"scrap_cost_pct": 2.5})
    )
    response = get_quality_scrap_cost_pct_series(
        branch="01",
        start_date="01-06-2026",
        end_date="30-06-2026",
        date_start=None,
        date_end=None,
        granularity="month",
    )
    body = body_json(response)
    assert_envelope_meta(body, operation_id="get_quality_scrap_cost_pct_series")
    assert body["meta"]["entity"] == "quality_scrap_cost_pct_series"
    assert body["data"]["points"]
    assert body["data"]["points"][0]["metrics"]["scrap_cost_pct"] == 2.5


@patch(f"{_LOSSES}.build_get_retrabalho_rework_cost_pct_use_case")
def test_get_quality_rework_cost_pct_series_returns_meta(mock_builder) -> None:
    from app.interface.http.routes.quality.losses_routes import (
        get_quality_rework_cost_pct_series,
    )

    mock_builder.return_value = MagicMock(
        execute=MagicMock(return_value={"rework_cost_pct": 1.2})
    )
    response = get_quality_rework_cost_pct_series(
        branch="01",
        start_date="01-06-2026",
        end_date="30-06-2026",
        date_start=None,
        date_end=None,
        granularity="month",
    )
    body = body_json(response)
    assert_envelope_meta(body, operation_id="get_quality_rework_cost_pct_series")
    assert body["meta"]["entity"] == "quality_rework_cost_pct_series"


@patch(f"{_Q}.build_get_kaizen_summary_use_case")
def test_get_kaizen_summary_series_returns_meta(mock_builder) -> None:
    from app.interface.http.routes.quality.quality_router import get_kaizen_summary_series

    summary = MagicMock()
    summary.to_dict.return_value = {"total_kaizens": 3, "total_savings": 100.0}
    mock_builder.return_value = MagicMock(execute=MagicMock(return_value=summary))

    response = get_kaizen_summary_series(
        branch="01",
        start_date="01-06-2026",
        end_date="30-06-2026",
        date_start=None,
        date_end=None,
        granularity="month",
    )
    body = body_json(response)
    assert_envelope_meta(body, operation_id="get_kaizen_summary_series")
    assert body["meta"]["entity"] == "kaizen_summary_series"
    assert body["data"]["points"][0]["metrics"]["total_kaizens"] == 3


@patch(f"{_Q}.build_get_audit_5s_summary_use_case")
def test_get_audit_5s_summary_series_returns_meta(mock_builder) -> None:
    from app.interface.http.routes.quality.quality_router import (
        get_audit_5s_summary_series,
    )

    summary = MagicMock()
    summary.to_dict.return_value = {"average_score": 8.5}
    mock_builder.return_value = MagicMock(execute=MagicMock(return_value=summary))

    response = get_audit_5s_summary_series(
        branch="01",
        start_date="01-06-2026",
        end_date="30-06-2026",
        granularity="month",
    )
    body = body_json(response)
    assert_envelope_meta(body, operation_id="get_audit_5s_summary_series")
    assert body["meta"]["entity"] == "audit_5s_summary_series"
    assert body["data"]["points"][0]["metrics"]["average_score"] == 8.5
