"""Smoke Fase 1b — commercial KPIs, production custos, engineering mini-app, inspeções, public."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"
_PRODUCTION = "app.interface.http.routes.production.production_router"
_ENGINEERING = "app.interface.http.routes.engineering.engineering_router"
_INSPECOES = "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router"


@pytest.mark.parametrize(
    ("handler_name", "builder_name", "operation_id", "with_segment"),
    [
        (
            "get_branch_rol_target_pct",
            "build_get_branch_rol_target_pct_use_case",
            "get_branch_rol_target_pct",
            True,
        ),
        (
            "get_branch_weg_rol_target_pct",
            "build_get_branch_weg_rol_target_use_case",
            "get_branch_weg_rol_target_pct",
            False,
        ),
        (
            "get_branch_new_business_rol_target_pct",
            "build_get_branch_new_business_rol_target_use_case",
            "get_branch_new_business_rol_target_pct",
            False,
        ),
        (
            "get_head_office_weg_rol_target_pct",
            "build_get_head_office_weg_rol_target_use_case",
            "get_head_office_weg_rol_target_pct",
            False,
        ),
        (
            "get_head_office_new_business_rol_target_pct",
            "build_get_head_office_new_business_rol_target_use_case",
            "get_head_office_new_business_rol_target_pct",
            False,
        ),
    ],
)
def test_commercial_rol_target_kpis_return_meta(
    handler_name: str,
    builder_name: str,
    operation_id: str,
    with_segment: bool,
) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    handler = getattr(router_mod, handler_name)
    with (
        patch(f"{_COMMERCIAL}.enrich_dashboard_metric", side_effect=lambda p, **_: p),
        patch(f"{_COMMERCIAL}.{builder_name}") as mock_build,
    ):
        mock_build.return_value = MagicMock(
            execute=MagicMock(return_value={"rol": 1.0, "target_pct": 10.0})
        )
        kwargs = {"start_date": None, "end_date": None}
        if with_segment:
            kwargs["customer_segment"] = None
        response = handler(**kwargs)
    assert_envelope_meta(body_json(response), operation_id=operation_id, shape="scalar")


@patch(f"{_COMMERCIAL}.build_get_new_clients_average_use_case")
def test_new_clients_average_returns_meta(mock_build) -> None:
    from app.interface.http.routes.commercial.commercial_router import (
        get_new_clients_average,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"average": 3.2})
    )
    response = get_new_clients_average(branch=None, start_date=None, end_date=None)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_new_clients_average",
        shape="scalar",
    )


@patch(f"{_COMMERCIAL}.build_get_new_clients_rol_pct_use_case")
def test_new_clients_rol_pct_returns_meta(mock_build) -> None:
    from app.interface.http.routes.commercial.commercial_router import (
        get_new_clients_rol_pct,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"rol_pct": 12.5})
    )
    response = get_new_clients_rol_pct(branch=None, start_date=None, end_date=None)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_new_clients_rol_pct",
        shape="scalar",
    )


@patch(f"{_COMMERCIAL}.build_get_sales_order_otd_series_use_case")
def test_sales_order_otd_series_returns_meta(mock_build) -> None:
    from app.interface.http.routes.commercial.commercial_router import (
        get_sales_order_otd_series,
    )

    result = MagicMock()
    result.to_dict.return_value = {"points": [], "granularity": "month"}
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))

    response = get_sales_order_otd_series(
        granularity="month",
        start_date=None,
        end_date=None,
        branch=None,
        customer_segment=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_sales_order_otd_series",
        shape="scalar",
    )


@patch(f"{_COMMERCIAL}.build_engineering_get_lmp_history_events_use_case")
def test_commercial_proposal_history_events_returns_meta(mock_build) -> None:
    from app.interface.http.routes.commercial.commercial_router import (
        get_commercial_proposal_history_events,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"items": [], "total": 0})
    )
    response = get_commercial_proposal_history_events(
        proposal_number="OV123",
        branch="01",
        revision=None,
        date_start=None,
        date_end=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_commercial_proposal_history_events",
        shape="paged_list",
    )


@pytest.mark.parametrize(
    ("handler_name", "builder_name", "operation_id"),
    [
        (
            "get_direct_labor_cost_pct",
            "build_get_direct_labor_cost_pct_use_case",
            "get_direct_labor_cost_pct",
        ),
        (
            "get_production_cost_pct",
            "build_get_production_cost_pct_use_case",
            "get_production_cost_pct",
        ),
        (
            "get_depreciation_pct",
            "build_get_depreciation_pct_use_case",
            "get_depreciation_pct",
        ),
    ],
)
def test_production_cost_kpis_return_meta(
    handler_name: str, builder_name: str, operation_id: str
) -> None:
    import app.interface.http.routes.production.production_router as router_mod

    handler = getattr(router_mod, handler_name)
    with (
        patch(f"{_PRODUCTION}.enrich_dashboard_metric", side_effect=lambda p, **_: p),
        patch(f"{_PRODUCTION}.{builder_name}") as mock_build,
    ):
        mock_build.return_value = MagicMock(
            execute=MagicMock(return_value={"value": 1.0})
        )
        response = handler(branch=None, start_date=None, end_date=None)
    assert_envelope_meta(body_json(response), operation_id=operation_id, shape="scalar")


@patch(f"{_ENGINEERING}.build_get_mini_applicators_ferramenta_use_case")
def test_mini_applicators_ferramenta_returns_meta(mock_build) -> None:
    from app.interface.http.routes.engineering.engineering_router import (
        get_mini_applicators_ferramenta_route,
    )

    result = MagicMock()
    result.to_dict.return_value = {"codigo": "F1", "descricao": "Ferramenta"}
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))

    response = get_mini_applicators_ferramenta_route(codigo="F1")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_mini_applicators_ferramenta",
        shape="scalar",
    )


@patch(f"{_ENGINEERING}.build_get_mini_applicators_golpes_use_case")
def test_mini_applicators_golpes_returns_meta(mock_build) -> None:
    from app.interface.http.routes.engineering.engineering_router import (
        get_mini_applicators_golpes_route,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"codigo": "F1", "golpes": 10})
    )

    response = get_mini_applicators_golpes_route(
        codigo="F1",
        filial="01",
        data_inicial="2026-01-01",
        data_final="2026-01-31",
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_mini_applicators_golpes",
        shape="scalar",
    )


@patch(f"{_ENGINEERING}.build_list_mini_applicators_pecas_use_case")
def test_mini_applicators_pecas_returns_meta(mock_build) -> None:
    from app.interface.http.routes.engineering.engineering_router import (
        list_mini_applicators_pecas_route,
    )

    mock_build.return_value = MagicMock(execute=MagicMock(return_value=[]))

    response = list_mini_applicators_pecas_route(codigo="F1")
    assert_envelope_meta(
        body_json(response),
        operation_id="list_mini_applicators_pecas",
        shape="list",
    )


@patch(f"{_ENGINEERING}.build_list_mini_applicators_pecas_reposicao_use_case")
def test_mini_applicators_pecas_reposicao_returns_meta(mock_build) -> None:
    from app.interface.http.routes.engineering.engineering_router import (
        list_mini_applicators_pecas_reposicao_route,
    )

    result = MagicMock()
    result.to_dict.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
    }
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))

    response = list_mini_applicators_pecas_reposicao_route(
        codigo=None,
        descricao=None,
        page=1,
        page_size=50,
        sort_by=None,
        sort_dir="asc",
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="list_mini_applicators_pecas_reposicao",
        shape="paged_list",
    )


@patch(f"{_INSPECOES}._branch_view_allowed", return_value=True)
@patch(f"{_INSPECOES}.build_list_inspecoes_entrada_rejeitadas_produto_use_case")
def test_inspecoes_entrada_rejeitadas_produto_returns_meta(
    mock_build, _mock_branch
) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_rejeitadas_produto_route,
    )

    result = MagicMock()
    result.to_dict.return_value = {
        "branch": "01",
        "items": [],
        "total_products": 0,
        "total_rejected": 0,
    }
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))

    response = get_inspecoes_entrada_rejeitadas_produto_route(branch="01", limit=50)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_inspecoes_entrada_rejeitadas_produto",
    )


@patch(
    "app.interface.http.routes.quality.kaizen_public_router.build_kaizen_repository"
)
@patch(
    "app.interface.http.routes.quality.kaizen_public_router.notify_public_suggestion_created"
)
def test_create_public_kaizen_suggestion_returns_meta(
    _mock_notify, mock_repo_build
) -> None:
    from app.interface.http.routes.quality.kaizen_public_router import (
        PublicKaizenSuggestionBody,
        create_public_kaizen_suggestion,
    )

    mock_repo_build.return_value = MagicMock(
        create_record=MagicMock(return_value={"id": "k-1"})
    )
    response = create_public_kaizen_suggestion(
        body=PublicKaizenSuggestionBody(
            proposer_name="Fulano Silva",
            sector="Produção",
            employee_registration="12345",
            work_center_or_location="CC01",
            problem_description="Problema detalhado",
            proposed_solution="Solução proposta",
            branch_code="01",
            website=None,
        )
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="create_public_kaizen_suggestion",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.quality.quality_labels_public_router.build_quality_labels_service"
)
def test_public_quality_label_inspection_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.quality_labels_public_router import (
        get_public_inspection,
    )

    mock_build.return_value = MagicMock(
        get_public=MagicMock(return_value={"token": "abc", "status": "ok"})
    )
    response = get_public_inspection(token="abc")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_public_quality_label_inspection",
    )
