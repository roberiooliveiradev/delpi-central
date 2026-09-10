"""E1.S6B — selection cutover: OpenAPI-first authority; markers/intent viram observer."""

from __future__ import annotations

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.services.openapi_tool_routing_content_service import (
    invalidate_openapi_tool_routing_cache,
)
from app.domain.services.registry_selection_shadow_observability_service import (
    RegistrySelectionShadowObservabilityService,
)


class _Repo:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        return [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ][:limit]

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []


def _catalog() -> list[dict]:
    return [
        {
            "actionId": "acme.products.stock",
            "method": "GET",
            "path": "/products/{code}/stock",
            "operationId": "get_product_stock",
            "summary": "Product stock balance by code",
            "description": "Saldo de estoque disponível por código de produto.",
            "whenToUse": "estoque, saldo disponível",
            "sensitivity": "read",
            "enabled": True,
        },
        {
            "actionId": "acme.products.search",
            "method": "GET",
            "path": "/products/search",
            "operationId": "search_products",
            "summary": "Search products by description",
            "description": "Busca produtos pela descrição sem código.",
            "whenToUse": "liste produtos, busque pela descrição",
            "sensitivity": "read",
            "enabled": True,
        },
        {
            "actionId": "acme.shipments.tracking",
            "method": "GET",
            "path": "/shipments/{id}/tracking",
            "operationId": "get_shipment_tracking",
            "summary": "Shipment tracking",
            "description": "Rastreio de remessa.",
            "whenToUse": "rastreio de remessa",
            "sensitivity": "read",
            "enabled": True,
        },
        {
            "actionId": "vendorx.widgets.balance",
            "method": "GET",
            "path": "/widgets/{id}/balance",
            "operationId": "get_widget_balance",
            "summary": "Unknown vendor widget balance",
            "description": "Saldo de widgets do provider vendorx.",
            "whenToUse": "saldo do widget, balance widget vendorx",
            "sensitivity": "read",
            "enabled": True,
        },
    ]


def _force_cutover_on(monkeypatch) -> None:
    from app.domain.services.openapi_tool_routing_content_service import (
        OpenApiToolRoutingContentService,
    )

    original = OpenApiToolRoutingContentService.bool_setting

    def _bool_setting(*path, default=False):
        if path[:2] == ("registrySelectionShadow", "cutoverEnabled"):
            return True
        if path[:2] == ("registrySelectionShadow", "enabled"):
            return True
        return original(*path, default=default)

    monkeypatch.setattr(OpenApiToolRoutingContentService, "bool_setting", _bool_setting)


def test_cutover_registry_prefers_retrieval_over_wrong_markers(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    _force_cutover_on(monkeypatch)
    catalog = _catalog()
    service = ExternalActionSelectionService(_Repo(catalog))
    ids = [row["actionId"] for row in catalog]

    monkeypatch.setattr(
        "app.domain.services.operational_route_registry_service."
        "OperationalRouteRegistryService.route_by_id",
        lambda _route_id: {
            "id": "product.stock",
            "route": {"pathMarkers": ["/stock"], "operationIdMarkers": ["stock"]},
        },
    )

    def _openapi(message, *, allowed_action_ids, **kwargs):
        # Mimic OpenAPI-first: among allowed, pick lexical winner.
        if set(allowed_action_ids) == set(ids):
            return {
                "actionId": "acme.shipments.tracking",
                "arguments": {"actionId": "acme.shipments.tracking", "parameters": {}},
                "metadata": {},
            }
        # Marker-narrowed legacy would still pick stock.
        return {
            "actionId": "acme.products.stock",
            "arguments": {"actionId": "acme.products.stock", "parameters": {}},
            "metadata": {},
        }

    monkeypatch.setattr(service, "_select_via_openapi_first", _openapi)

    selected = service.select_registry_route_id(
        "product.stock",
        "onde está a remessa 45871",
        allowed_action_ids=ids,
    )
    assert selected is not None
    assert selected["actionId"] == "acme.shipments.tracking"
    shadow = (selected.get("metadata") or {}).get("registrySelectionShadow")
    assert shadow["cutover"] is True
    assert shadow["authorityActionId"] == "acme.shipments.tracking"
    assert shadow["legacyActionId"] == "acme.products.stock"
    assert shadow["agree"] is True  # authority ∈ candidate top-K


def test_cutover_product_intent_prefers_retrieval(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    _force_cutover_on(monkeypatch)
    catalog = _catalog()
    service = ExternalActionSelectionService(_Repo(catalog))
    ids = [row["actionId"] for row in catalog]

    monkeypatch.setattr(
        service,
        "_select_via_openapi_first",
        lambda *args, **kwargs: {
            "actionId": "acme.shipments.tracking",
            "arguments": {"actionId": "acme.shipments.tracking", "parameters": {}},
            "metadata": {},
        },
    )
    monkeypatch.setattr(
        service,
        "_select_product_action",
        lambda *args, **kwargs: {
            "arguments": {"actionId": "acme.products.stock", "parameters": {}},
        },
    )

    selected = service.select_action_for_product(
        "onde está a remessa 45871",
        product_code="10080047",
        allowed_action_ids=ids,
        intent="stock",
        route_segment="stock",
    )
    assert selected["actionId"] == "acme.shipments.tracking"
    shadow = (selected.get("metadata") or {}).get("productSelectionShadow")
    assert shadow["cutover"] is True
    assert shadow["authorityActionId"] == "acme.shipments.tracking"
    assert shadow["legacyActionId"] == "acme.products.stock"


def test_cutover_unknown_provider_without_markers(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    _force_cutover_on(monkeypatch)
    catalog = _catalog()
    service = ExternalActionSelectionService(_Repo(catalog))
    ids = [row["actionId"] for row in catalog]

    monkeypatch.setattr(
        "app.domain.services.operational_route_registry_service."
        "OperationalRouteRegistryService.route_by_id",
        lambda _route_id: {
            "id": "vendorx.widgets",
            "route": {"pathMarkers": ["/does-not-match"], "operationIdMarkers": []},
        },
    )
    monkeypatch.setattr(
        service,
        "_select_via_openapi_first",
        lambda message, *, allowed_action_ids, **kwargs: {
            "actionId": "vendorx.widgets.balance",
            "arguments": {"actionId": "vendorx.widgets.balance", "parameters": {}},
            "metadata": {},
        }
        if "vendorx.widgets.balance" in allowed_action_ids
        else None,
    )

    selected = service.select_registry_route_id(
        "vendorx.widgets",
        "saldo do widget vendorx",
        allowed_action_ids=ids,
    )
    assert selected is not None
    assert selected["actionId"] == "vendorx.widgets.balance"


def test_cutover_metamorphic_rename_preserves_authority(monkeypatch):
    invalidate_openapi_tool_routing_cache()
    _force_cutover_on(monkeypatch)
    renamed = [
        {
            **row,
            "actionId": row["actionId"].replace("acme.", "acme2."),
            "path": row["path"].replace("/products/", "/items/").replace(
                "/shipments/", "/deliveries/"
            ),
            "operationId": row["operationId"] + "_v2",
        }
        for row in _catalog()
        if row["actionId"].startswith("acme.")
    ]
    service = ExternalActionSelectionService(_Repo(renamed))
    ids = [row["actionId"] for row in renamed]

    monkeypatch.setattr(
        "app.domain.services.operational_route_registry_service."
        "OperationalRouteRegistryService.route_by_id",
        lambda _route_id: {
            "id": "product.stock",
            "route": {"pathMarkers": ["/stock"], "operationIdMarkers": ["stock"]},
        },
    )
    monkeypatch.setattr(
        service,
        "_select_via_openapi_first",
        lambda message, *, allowed_action_ids, **kwargs: {
            "actionId": "acme2.products.stock",
            "arguments": {"actionId": "acme2.products.stock", "parameters": {}},
            "metadata": {},
        },
    )

    selected = service.select_registry_route_id(
        "product.stock",
        "qual o estoque do produto 10080047",
        allowed_action_ids=ids,
    )
    assert selected["actionId"] == "acme2.products.stock"


def test_cutover_corpus_agree_rate_gate(monkeypatch):
    """Offline corpus ≥20 samples: authority cutover agrees with retrieval top-K."""
    invalidate_openapi_tool_routing_cache()
    _force_cutover_on(monkeypatch)
    catalog = _catalog()
    service = ExternalActionSelectionService(_Repo(catalog))
    ids = [row["actionId"] for row in catalog]

    bases = [
        ("estoque do produto", "acme.products.stock"),
        ("saldo disponível do produto", "acme.products.stock"),
        ("quantas unidades em estoque", "acme.products.stock"),
        ("consultar estoque por código", "acme.products.stock"),
        ("liste produtos pela descrição", "acme.products.search"),
        ("busque produtos terminal pino", "acme.products.search"),
        ("busque pela descrição cabo", "acme.products.search"),
        ("liste produtos do catálogo", "acme.products.search"),
        ("rastreio da remessa", "acme.shipments.tracking"),
        ("onde está a remessa", "acme.shipments.tracking"),
        ("status de rastreio da remessa", "acme.shipments.tracking"),
        ("acompanhar remessa", "acme.shipments.tracking"),
        ("saldo do widget vendorx", "vendorx.widgets.balance"),
        ("saldo de widgets vendorx", "vendorx.widgets.balance"),
    ]
    prefixes = ["", "preciso de ", "pode verificar ", "consulta: "]
    corpus: list[tuple[str, str]] = []
    for base, action_id in bases:
        for prefix in prefixes:
            corpus.append((f"{prefix}{base}".strip(), action_id))
    assert len(corpus) >= 20

    monkeypatch.setattr(
        "app.domain.services.operational_route_registry_service."
        "OperationalRouteRegistryService.route_by_id",
        lambda _route_id: {
            "id": "generic",
            "route": {"pathMarkers": ["/"], "operationIdMarkers": []},
        },
    )

    samples = []
    divergences = []
    for message, expected in corpus:
        monkeypatch.setattr(
            service,
            "_select_via_openapi_first",
            lambda message, *, allowed_action_ids, expected=expected, **kwargs: {
                "actionId": expected,
                "arguments": {"actionId": expected, "parameters": {}},
                "metadata": {},
            },
        )
        selected = service.select_registry_route_id(
            "generic",
            message,
            allowed_action_ids=ids,
        )
        assert selected is not None
        shadow = (selected.get("metadata") or {}).get("registrySelectionShadow")
        assert isinstance(shadow, dict)
        samples.append(shadow)
        if not shadow.get("agree"):
            divergences.append((message, expected, shadow.get("candidateTopIds")))

    summary = RegistrySelectionShadowObservabilityService.aggregate_snapshots(
        [{"snapshot": samples, "loggedAt": "2026-09-10T12:00:00Z", "action": "test"}],
        hours=24,
        since_iso="2026-09-09T12:00:00Z",
    )
    assert not divergences, divergences
    assert summary["samplesCount"] >= 20
    assert summary["agreeRate"] == 1.0
    assert summary["cutoverReadyHint"] == "candidate"
