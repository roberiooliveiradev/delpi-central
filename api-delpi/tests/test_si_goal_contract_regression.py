"""Regression: SI goal triad across all *_meta TV catalog routes + hub enrich."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.services.strategic_indicators.dashboard_goals_service import (
    DashboardGoalsService,
)
from app.application.services.strategic_indicators.dashboard_si_indicator_metric_service import (
    DashboardSiIndicatorMetricService,
)
from app.application.services.strategic_indicators.si_indicator_tv_catalog import (
    load_si_indicator_tv_catalog,
    operation_id_for,
    path_for,
)
from app.interface.http.kpi_field_labels import SI_GOAL_FIELD_LABELS
from app.interface.http.route_contract_registry import resolve_contract
from app.interface.http.routes.dashboard.dashboard_router import (
    _SI_INDICATOR_SCALAR_FIELDS,
    router,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import (
    enrich_dashboard_metric,
)
from tests.fixtures.si_goal_contract_cases import (
    HUB_ENRICH_CASES,
    PARTIAL_SI_META_PAYLOAD,
    SI_GOAL_FIELD_LABELS_PT,
)
from tests.support.route_contract_smoke import assert_envelope_meta
from tests.support.si_indicator_tv_operation_ids import SI_INDICATOR_TV_OPERATION_IDS

_META_OPERATION_IDS = tuple(
    op for op in SI_INDICATOR_TV_OPERATION_IDS if op.endswith("_meta")
)
_CATALOG_META_ROWS = [
    (row["indicator_id"], operation_id_for(row["indicator_id"], "meta"))
    for row in load_si_indicator_tv_catalog()
]


def test_meta_operation_ids_match_catalog() -> None:
    catalog_ops = {op for _, op in _CATALOG_META_ROWS}
    assert set(_META_OPERATION_IDS) == catalog_ops
    assert len(_META_OPERATION_IDS) >= 30


@pytest.mark.parametrize("operation_id", _META_OPERATION_IDS)
def test_meta_operation_contract_is_scalar(operation_id: str) -> None:
    entity, shape = resolve_contract(operation_id)
    assert entity == "dashboard_si_indicator_meta"
    assert shape == "scalar"


@pytest.mark.parametrize(
    "indicator_id,operation_id",
    _CATALOG_META_ROWS,
    ids=[op for _, op in _CATALOG_META_ROWS],
)
def test_meta_route_preserves_partial_triad(
    indicator_id: str, operation_id: str
) -> None:
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    payload = {
        "indicator_id": indicator_id,
        "name": indicator_id,
        **PARTIAL_SI_META_PAYLOAD,
    }

    with patch(
        "app.interface.http.routes.dashboard.dashboard_router."
        "get_dashboard_si_indicator_metric_service"
    ) as mock_svc:
        mock_svc.return_value.get_metric.return_value = payload
        response = client.get(
            f"/dashboard{path_for(indicator_id, 'meta')}",
            params={"start_date": "2026-08-01", "end_date": "2026-08-17"},
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert_envelope_meta(
        body,
        operation_id=operation_id,
        shape="scalar",
        entity="dashboard_si_indicator_meta",
    )
    data = body["data"]
    assert data["goal_value"] == 10.0
    assert data["comparable_goal"] == 5.0
    assert data["reference_goal"] == 10.0
    assert data["value"] == 5.0
    assert data["goal_value"] != data["comparable_goal"]

    fields = body["meta"].get("fields") or {}
    for key, label in SI_GOAL_FIELD_LABELS_PT.items():
        assert fields.get(key) == label, (operation_id, key, fields.get(key))
        assert _SI_INDICATOR_SCALAR_FIELDS.get(key) == label


def test_flatten_goal_keeps_registered_distinct_from_comparable() -> None:
    flattened = DashboardGoalsService._flatten_goal(PARTIAL_SI_META_PAYLOAD)
    assert flattened["goal_value"] == 10.0
    assert flattened["comparable_goal"] == 5.0
    assert flattened["reference_goal"] == 10.0
    assert flattened["target"] == 5.0
    assert flattened["goal_value"] != flattened["comparable_goal"]


def test_metric_service_passes_through_partial_triad() -> None:
    mock_client = MagicMock()
    mock_client.get_dashboard_indicator_meta.return_value = {
        "indicator_id": "quality-kaizen-ideas",
        **PARTIAL_SI_META_PAYLOAD,
    }
    service = DashboardSiIndicatorMetricService(client=mock_client)
    result = service.get_metric(
        indicator_id="quality-kaizen-ideas",
        kind="meta",
        start_date="2026-08-01",
        end_date="2026-08-17",
    )
    assert result["goal_value"] == 10.0
    assert result["comparable_goal"] == 5.0
    assert result["reference_goal"] == 10.0
    assert result["value"] == 5.0


@pytest.mark.parametrize("case", HUB_ENRICH_CASES, ids=lambda c: c["id"])
def test_hub_enrich_preserves_partial_triad(case: dict) -> None:
    service = DashboardGoalsService()
    goal = {
        "source_key": case["source_key"],
        **PARTIAL_SI_META_PAYLOAD,
        "goal_label": "Meta",
    }
    with (
        patch.object(service, "get_goal", return_value=goal),
        patch(
            "app.application.services.strategic_indicators.dashboard_goals_service."
            "get_dashboard_goals_service",
            return_value=service,
        ),
    ):
        result = enrich_dashboard_metric(
            case["payload"],
            source_key=case["source_key"],
            summary_key=case["summary_key"],
            start_date="2026-08-01",
            end_date="2026-08-17",
        )

    target = (
        result[case["summary_key"]]
        if case["summary_key"]
        else result
    )
    assert target["goal_value"] == 10.0
    assert target["comparable_goal"] == 5.0
    assert target["reference_goal"] == 10.0
    assert target["goal_value"] != target["comparable_goal"]


def test_si_goal_field_labels_canonical() -> None:
    for key, label in SI_GOAL_FIELD_LABELS_PT.items():
        assert SI_GOAL_FIELD_LABELS[key] == label
