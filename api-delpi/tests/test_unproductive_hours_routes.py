"""Smoke e unitários — /production/unproductive-hours."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.services.response_meta_builder import DATA_VERSION


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def unproductive_hours_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.production.unproductive_hours_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_summary_items_ranking(
    unproductive_hours_client: TestClient,
) -> None:
    from app.interface.http.routes.production.unproductive_hours_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/production/unproductive-hours"
    assert "/production/unproductive-hours/summary" in paths
    assert "/production/unproductive-hours/items" in paths
    assert "/production/unproductive-hours/ranking" in paths


@patch(
    "app.interface.http.routes.production.unproductive_hours_router"
    ".build_get_production_unproductive_hours_summary_use_case"
)
def test_summary_returns_envelope(mock_builder, unproductive_hours_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "periodo": {"dataInicio": "2025-07-01", "dataFim": "2026-07-01", "filial": "01"},
        "summary": {
            "totalApontamentos": 10,
            "totalHoras": 20.5,
            "totalCusto": 100.0,
            "custoMedioHora": 4.88,
            "registrosSemCusto": 1,
            "horasSemCusto": 1.0,
            "percentualHorasSemCusto": 4.88,
            "principalRecursoPorHoras": None,
            "principalColaboradorPorHoras": None,
        },
    }
    mock_builder.return_value = use_case

    response = unproductive_hours_client.get(
        "/production/unproductive-hours/summary",
        params={"branch": "01", "start_date": "2025-07-01", "end_date": "2026-07-01"},
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["success"] is True
    assert payload["meta"]["operationId"] == "get_production_unproductive_hours_summary"
    assert payload["meta"]["entity"] == "production_unproductive_hours_summary"
    assert payload["meta"]["shape"] == "playbook_report"
    assert payload["meta"]["dataVersion"] == DATA_VERSION
    assert payload["data"]["summary"]["totalHoras"] == 20.5


@patch(
    "app.interface.http.routes.production.unproductive_hours_router"
    ".build_get_production_unproductive_hours_items_use_case"
)
def test_items_returns_envelope_with_motivo_descricao(
    mock_builder, unproductive_hours_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "periodo": {"dataInicio": "2025-07-01", "dataFim": "2026-07-01", "filial": "01"},
        "items": [
            {
                "dataReferencia": "2026-01-15",
                "filial": "01",
                "motivo": "RT",
                "motivoDescricao": "RETRABALHO",
                "tempoHoras": 1.5,
            }
        ],
        "page": 1,
        "pageSize": 50,
        "total": 1,
        "totalPages": 1,
        "sort": "date_desc",
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
            "is_complete": True,
        },
    }
    mock_builder.return_value = use_case

    response = unproductive_hours_client.get(
        "/production/unproductive-hours/items",
        params={"branch": "01", "start_date": "2025-07-01", "end_date": "2026-07-01"},
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["meta"]["operationId"] == "get_production_unproductive_hours_items"
    assert payload["meta"]["entity"] == "production_unproductive_hours_item"
    assert payload["meta"]["shape"] == "paged_list"
    assert payload["data"]["items"][0]["motivoDescricao"] == "RETRABALHO"
    assert payload["data"]["items"][0]["dataReferencia"] == "2026-01-15"


@patch(
    "app.interface.http.routes.production.unproductive_hours_router"
    ".build_get_production_unproductive_hours_ranking_use_case"
)
def test_ranking_returns_envelope(mock_builder, unproductive_hours_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "periodo": {"dataInicio": "2025-07-01", "dataFim": "2026-07-01", "filial": None},
        "rankBy": "stop_reason",
        "metric": "hours",
        "limit": 10,
        "items": [
            {
                "rank": 1,
                "motivo": "OT",
                "motivoDescricao": "OUTROS (JUSTIFICAR)",
                "totalHoras": 100.0,
                "totalCusto": 50.0,
            }
        ],
    }
    mock_builder.return_value = use_case

    response = unproductive_hours_client.get(
        "/production/unproductive-hours/ranking",
        params={
            "rank_by": "stop_reason",
            "start_date": "2025-07-01",
            "end_date": "2026-07-01",
        },
    )
    assert response.status_code == 200
    payload = _body(response)
    assert payload["meta"]["operationId"] == "get_production_unproductive_hours_ranking"
    assert payload["meta"]["entity"] == "production_unproductive_hours_ranking"
    assert payload["meta"]["shape"] == "list"
    assert payload["data"]["items"][0]["motivo"] == "OT"


def test_ranking_requires_rank_by(unproductive_hours_client: TestClient) -> None:
    response = unproductive_hours_client.get(
        "/production/unproductive-hours/ranking",
        params={"start_date": "2025-07-01", "end_date": "2026-07-01"},
    )
    assert response.status_code == 422


def test_ranking_invalid_rank_by_pattern(unproductive_hours_client: TestClient) -> None:
    response = unproductive_hours_client.get(
        "/production/unproductive-hours/ranking",
        params={
            "rank_by": "not_a_dimension",
            "start_date": "2025-07-01",
            "end_date": "2026-07-01",
        },
    )
    assert response.status_code == 422
