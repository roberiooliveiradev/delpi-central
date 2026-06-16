from unittest.mock import MagicMock

from app.application.services.external_actions.external_action_registry_dispatch_phase_service import (
    ExternalActionRegistryDispatchPhaseService,
    RegistryDispatchCallbacks,
    RegistryDispatchContext,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def _context(**overrides) -> RegistryDispatchContext:
    base = {
        "message": "roteiro do produto 90260142",
        "normalized": "roteiro do produto 90260142",
        "sql_source": "roteiro do produto 90260142",
        "allowed_action_ids": ["guide"],
        "conversation_context": None,
        "previous_messages": None,
        "product_code": "90260142",
        "bound_product_intent": ChatProductQueryIntent.FULL,
        "product_route_segment": None,
    }
    base.update(overrides)
    return RegistryDispatchContext(**base)


def _callbacks(**overrides) -> RegistryDispatchCallbacks:
    base = {
        "candidates_loader": MagicMock(return_value=[]),
        "build_date_branch_parameters": MagicMock(return_value={}),
        "merge_date_parameters": MagicMock(side_effect=lambda _a, _m, params, **_: params),
        "path_lookup_loader": MagicMock(return_value=[]),
        "rank_candidates": MagicMock(side_effect=lambda _m, candidates, **_: candidates),
        "extract_sale_number": MagicMock(return_value=None),
        "select_product": MagicMock(return_value=None),
        "select_lmp": MagicMock(return_value=None),
        "select_sql": MagicMock(return_value=None),
        "resolve_previous_external_action_id": MagicMock(return_value=None),
        "clamp_max_depth_for_path": MagicMock(side_effect=lambda value, path: value),
    }
    base.update(overrides)
    return RegistryDispatchCallbacks(**base)


def test_dispatch_order_matches_registry() -> None:
    assert OperationalRouteRegistryService.dispatch_order() == [
        "sessionRefinement",
        "productionOperational",
        "operationalRoutes",
        "domainRoutes",
        "intentBoundRoutes",
        "sqlFallback",
        "semanticFallback",
    ]


def test_operational_routes_phase_runs_before_domain_routes() -> None:
    route_selection = MagicMock()
    route_selection.select_operational_registry.return_value = {
        "name": "execute_external_action",
        "arguments": {"actionId": "guide", "parameters": {}},
    }
    route_selection.select_department_kpi.return_value = None

    service = ExternalActionRegistryDispatchPhaseService(route_selection)
    selected = service.run(
        _context(),
        callbacks=_callbacks(),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "guide"
    route_selection.select_operational_registry.assert_called_once()
    route_selection.select_department_kpi.assert_not_called()


def test_domain_routes_run_when_operational_routes_miss() -> None:
    route_selection = MagicMock()
    route_selection.select_operational_registry.return_value = None
    route_selection.select_department_kpi.return_value = {
        "name": "execute_external_action",
        "arguments": {"actionId": "cpv", "parameters": {}},
    }

    service = ExternalActionRegistryDispatchPhaseService(route_selection)
    selected = service.run(
        _context(
            message="cpv suprimentos",
            normalized="cpv suprimentos",
            product_code=None,
        ),
        callbacks=_callbacks(),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "cpv"
    route_selection.select_department_kpi.assert_called_once()


def test_intent_bound_routes_run_after_domain_routes() -> None:
    route_selection = MagicMock()
    route_selection.select_operational_registry.return_value = None
    route_selection.select_department_kpi.return_value = None
    route_selection.select_lmp.return_value = None
    route_selection.select_kpi_without_product.return_value = None
    route_selection.select_intent_bound_route.return_value = {
        "name": "execute_external_action",
        "arguments": {"actionId": "stock-action", "parameters": {}},
    }

    service = ExternalActionRegistryDispatchPhaseService(route_selection)
    selected = service.run(
        _context(
            message="estoque do produto 90260142",
            normalized="estoque do produto 90260142",
            bound_product_intent=ChatProductQueryIntent.STOCK,
        ),
        callbacks=_callbacks(),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "stock-action"
    route_selection.select_intent_bound_route.assert_called_once()
