"""Regressão: build_parameters product_code não levanta NameError em memory_snapshot."""

from __future__ import annotations

from app.application.services.external_actions.operational_route_selection.operational_route_action_resolver_service import (
    OperationalRouteActionResolverService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()


class _FakeCatalog:
    def build_product_parameters(self, action, identifier, **kwargs):
        return {"code": identifier}

    def filter_parameters_to_schema(self, action, parameters):
        return parameters


def test_build_parameters_product_code_resolves_memory_snapshot_without_name_error():
    resolver = OperationalRouteActionResolverService(_FakeCatalog())
    route = {"parameters": {"strategy": "product_code"}}
    action = {
        "path": "/products/{code}/stock",
        "parametersSchema": [{"name": "code"}],
    }

    # Sem identifier na mensagem — cai no resolve_product_code(..., memory_snapshot=...)
    params = resolver.build_parameters(
        route,
        action,
        message="estoque",
        identifier=None,
        memory_snapshot={"operationalFocus": {"productCode": "10080047"}},
    )

    assert params == {"code": "10080047"}


def test_build_parameters_product_code_without_snapshot_uses_grounding_context():
    resolver = OperationalRouteActionResolverService(_FakeCatalog())
    route = {"parameters": {"strategy": "product_code"}}
    action = {
        "path": "/products/{code}/stock",
        "parametersSchema": [{"name": "code"}],
    }

    # Não deve levantar NameError mesmo sem snapshot (cai no grounding context / None)
    params = resolver.build_parameters(
        route,
        action,
        message="estoque",
        identifier=None,
        memory_snapshot=None,
    )
    assert params is None or isinstance(params, dict)
