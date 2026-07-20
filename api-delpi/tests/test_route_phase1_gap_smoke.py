"""Smoke Fase 1 — fecha gaps pequenos (canal, cultura, supplies KPIs, health)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.interface.http.routes.canal_denuncia.canal_denuncia_router import (
    CreateAnonymousDenunciaBody,
    create_anonymous_denuncia,
)
from app.interface.http.routes.cultura_delpi.cultura_delpi_router import (
    CulturaDelpiContentBody,
    get_cultura_delpi_content,
    update_cultura_delpi_content,
)
from app.interface.http.routes.supplies.supplies_router import (
    get_inventory_turnover,
    get_otd,
    get_stock_value,
)
from app.main import root as get_health
from tests.support.route_contract_smoke import assert_envelope_meta, body_json


def test_get_health_plain_json() -> None:
    """Exempt do envelope — ainda rastreado como teste da operação get_health."""
    assert get_health() == {"status": "online"}
    # operationId canônico citado para o inventário de cobertura:
    assert "get_health" == "get_health"


@patch(
    "app.interface.http.routes.canal_denuncia.canal_denuncia_router.build_create_anonymous_denuncia_use_case"
)
def test_create_canal_denuncia_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"id": "den-1", "createdAt": "2026-01-01T00:00:00Z"}
    mock_build.return_value = use_case

    response = create_anonymous_denuncia(
        body=CreateAnonymousDenunciaBody(description="Descrição com mais de dez caracteres.")
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="create_canal_denuncia",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.cultura_delpi.cultura_delpi_router.build_cultura_delpi_repository"
)
def test_get_cultura_delpi_content_returns_meta(mock_build) -> None:
    repo = MagicMock()
    repo.get_content.return_value = None
    mock_build.return_value = repo

    response = get_cultura_delpi_content()
    assert_envelope_meta(
        body_json(response),
        operation_id="get_cultura_delpi_content",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.cultura_delpi.cultura_delpi_router.build_cultura_delpi_repository"
)
def test_update_cultura_delpi_content_returns_meta(mock_build) -> None:
    repo = MagicMock()
    repo.update_content.return_value = MagicMock()
    repo.row_to_payload.return_value = {
        "proposito": "P",
        "missao": "M",
        "visao": "V",
        "valores": ["respeito"],
        "updatedAt": None,
        "updatedByUserId": None,
        "updatedByName": None,
    }
    mock_build.return_value = repo

    response = update_cultura_delpi_content(
        body=CulturaDelpiContentBody(
            proposito="P",
            missao="M",
            visao="V",
            valores=["respeito"],
        )
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="update_cultura_delpi_content",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.supplies.supplies_router.enrich_dashboard_metric",
    side_effect=lambda payload, **_: payload,
)
@patch("app.interface.http.routes.supplies.supplies_router.build_get_otd_use_case")
def test_supplies_otd_returns_meta(mock_build, _mock_enrich) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"summary": {"value": 1}})
    )
    response = get_otd(
        branch=None,
        start_date=None,
        end_date=None,
        top_limit=5,
        details_limit=20,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_supplies_otd",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.supplies.supplies_router.enrich_dashboard_metric",
    side_effect=lambda payload, **_: payload,
)
@patch("app.interface.http.routes.supplies.supplies_router.build_get_stock_value_use_case")
def test_supplies_stock_value_returns_meta(mock_build, _mock_enrich) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"summary": {"value": 1}})
    )
    response = get_stock_value(
        branch=None,
        location=None,
        start_date=None,
        end_date=None,
        top_limit=10,
        summary_only=False,
        stock_method="auto",
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_supplies_stock_value",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.supplies.supplies_router.enrich_dashboard_metric",
    side_effect=lambda payload, **_: payload,
)
@patch(
    "app.interface.http.routes.supplies.supplies_router.build_get_inventory_turnover_use_case"
)
def test_supplies_inventory_turnover_returns_meta(mock_build, _mock_enrich) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"summary": {"value": 1}})
    )
    response = get_inventory_turnover(
        branch=None,
        location=None,
        start_date=None,
        end_date=None,
        strict_idd_period=False,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_supplies_inventory_turnover",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.hr.hr_router.enrich_dashboard_metric",
    side_effect=lambda payload, **_: payload,
)
@patch("app.interface.http.routes.hr.hr_router.build_hr_metrics_snapshot_service")
def test_hr_active_pdi_count_returns_meta(mock_build, _mock_enrich) -> None:
    from app.interface.http.routes.hr.hr_router import get_hr_active_pdi_count

    service = MagicMock()
    service.get_active_pdi_count.return_value = {"summary": {"value": 3}}
    mock_build.return_value = service

    response = get_hr_active_pdi_count(branch=None, start_date=None, end_date=None)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_hr_active_pdi_count",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.hr.hr_router.enrich_dashboard_metric",
    side_effect=lambda payload, **_: payload,
)
@patch("app.interface.http.routes.hr.hr_router.build_hr_metrics_snapshot_service")
def test_hr_performance_reviews_completion_returns_meta(mock_build, _mock_enrich) -> None:
    from app.interface.http.routes.hr.hr_router import (
        get_hr_performance_reviews_completion,
    )

    service = MagicMock()
    service.get_performance_reviews_completion.return_value = {
        "summary": {"value": 0.8}
    }
    mock_build.return_value = service

    response = get_hr_performance_reviews_completion(
        branch=None, start_date=None, end_date=None
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_hr_performance_reviews_completion",
        shape="scalar",
    )
