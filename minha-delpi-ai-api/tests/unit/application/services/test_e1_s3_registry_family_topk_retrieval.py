"""E1.S3 — top-K recall for registry-like families without OperationalRouteRegistry.

Synthetic Action Catalog (no pathMarkers / operationIdMarkers / routeSegment).
Proves RetrieveActionCandidatesService can rank product_search, stock, description,
production and KPI siblings by OpenAPI prose alone.
"""

from __future__ import annotations

import pytest

from app.application.services.retrieve_action_candidates_service import (
    RetrieveActionCandidatesService,
)


def _action(**overrides) -> dict:
    payload = {
        "method": "GET",
        "sensitivity": "read",
        "enabled": True,
        "parametersSchema": [],
        "tags": [],
    }
    payload.update(overrides)
    return payload


def _catalog() -> list[dict]:
    """Registry-like families + distractors; paths are fictional vendor shapes."""
    return [
        _action(
            actionId="acme.products.search",
            path="/catalog/items/lookup",
            operationId="lookup_catalog_items",
            summary="Search products by description, group or free text",
            description=(
                "Busca produtos pela descrição, grupo ou texto livre. "
                "Use para listar ou pesquisar itens sem código conhecido. "
                "Não use para saldo de estoque nem descrição de um código específico."
            ),
            whenToUse=(
                "liste produtos, busque pela descrição, top N itens, pesquisar grupo"
            ),
            whenNotToUse="saldo estoque, descrição do produto com código",
            parametersSchema=[
                {
                    "name": "q",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                    "description": "free text search",
                }
            ],
            tags=["products", "search"],
        ),
        _action(
            actionId="acme.products.stock",
            path="/catalog/items/{code}/balance",
            operationId="get_item_balance",
            summary="Product stock balance by code",
            description=(
                "Saldo de estoque disponível por código de produto e filial. "
                "Use quando o usuário pede estoque, saldo ou disponibilidade "
                "de um produto conhecido."
            ),
            whenToUse="estoque, saldo disponível, quantas unidades do produto",
            whenNotToUse="buscar produtos pela descrição sem código",
            parametersSchema=[
                {
                    "name": "code",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            ],
            tags=["products", "stock"],
        ),
        _action(
            actionId="acme.products.description",
            path="/catalog/items/{code}/card",
            operationId="get_item_card",
            summary="Product description and cadastro card",
            description=(
                "Descrição cadastral e dados do produto por código. "
                "Use para «qual a descrição do produto» ou ficha técnica."
            ),
            whenToUse="descrição do produto, cadastro, ficha do item",
            whenNotToUse="estoque ou busca por texto",
            parametersSchema=[
                {
                    "name": "code",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            ],
            tags=["products", "description"],
        ),
        _action(
            actionId="acme.production.schedule",
            path="/plant/schedule/today",
            operationId="get_plant_schedule_today",
            summary="Today production schedule",
            description=(
                "Agenda de produção do dia na planta. "
                "Use para ordens de produção, programação e o que está rodando hoje."
            ),
            whenToUse="produção hoje, agenda de produção, ordens programadas",
            whenNotToUse="estoque de produto acabado ou KPI de receita",
            tags=["production"],
        ),
        _action(
            actionId="acme.kpi.site-revenue",
            path="/analytics/sites/{site}/revenue",
            operationId="get_site_revenue_kpi",
            summary="Scalar revenue KPI for one site",
            description=(
                "KPI escalar de receita de um site/filial. "
                "Use para «receita da filial» consolidada, não ranking tabular."
            ),
            whenToUse="receita da filial, KPI consolidado de um site",
            whenNotToUse="receita por site em tabela comparativa",
            parametersSchema=[
                {
                    "name": "site",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            ],
            tags=["kpi", "revenue"],
        ),
        _action(
            actionId="acme.kpi.revenue-by-site",
            path="/analytics/revenue/by-site",
            operationId="list_revenue_by_site",
            summary="Revenue breakdown by site",
            description=(
                "Ranking tabular de receita por site. "
                "Use para «receita por filial» comparativo."
            ),
            whenToUse="receita por filial, ranking de sites",
            whenNotToUse="receita consolidada de um único site",
            tags=["kpi", "revenue"],
        ),
        # Distractors
        _action(
            actionId="acme.warehouses.list",
            path="/warehouses",
            operationId="list_warehouses",
            summary="List warehouses",
            description="Lista depósitos e armazéns cadastrados.",
            whenToUse="listar armazéns",
            tags=["warehouses"],
        ),
        _action(
            actionId="acme.shipments.tracking",
            path="/shipments/{id}/tracking",
            operationId="get_shipment_tracking",
            summary="Shipment tracking",
            description="Rastreio de remessa logística.",
            whenToUse="rastreio de remessa",
            tags=["logistics"],
        ),
    ]


def _metamorphic_catalog(base: list[dict]) -> list[dict]:
    """Rename path/operationId/actionId; keep summary/description/whenToUse stable."""
    renamed = []
    for idx, row in enumerate(base):
        clone = dict(row)
        clone["actionId"] = f"vendor.renamed.{idx}"
        clone["path"] = f"/v2/renamed/{idx}"
        clone["operationId"] = f"renamed_op_{idx}"
        renamed.append(clone)
    return renamed


class _Repo:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        return [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ][:limit]

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []


def _allowed(actions: list[dict]) -> list[str]:
    return [str(item["actionId"]) for item in actions]


def _top_ids(message: str, catalog: list[dict], *, top_k: int = 5) -> list[str]:
    candidates = RetrieveActionCandidatesService(_Repo(catalog)).retrieve(
        message,
        allowed_action_ids=_allowed(catalog),
        catalog_actions=catalog,
        top_k=top_k,
    )
    return [item.action_id for item in candidates]


CASES = [
    pytest.param(
        "liste os top 50 terminais pino",
        "acme.products.search",
        id="product_search",
    ),
    pytest.param(
        "qual o estoque do produto 10080047",
        "acme.products.stock",
        id="product_stock",
    ),
    pytest.param(
        "qual a descrição do produto 10080047",
        "acme.products.description",
        id="product_description",
    ),
    pytest.param(
        "o que está na agenda de produção hoje",
        "acme.production.schedule",
        id="production_schedule",
    ),
    pytest.param(
        "qual a receita consolidada da filial 01",
        "acme.kpi.site-revenue",
        id="kpi_scalar",
    ),
]


@pytest.mark.parametrize("message,expected", CASES)
def test_registry_family_expected_action_in_topk(message, expected):
    catalog = _catalog()
    ids = _top_ids(message, catalog)
    assert expected in ids, f"expected {expected} in top-K {ids} for {message!r}"


def test_sibling_kpi_breakdown_not_scalar():
    catalog = _catalog()
    ids = _top_ids("mostre a receita por filial em ranking", catalog)
    assert "acme.kpi.revenue-by-site" in ids
    assert ids[0] == "acme.kpi.revenue-by-site"


def test_negative_tracking_not_forced_to_product_search():
    catalog = _catalog()
    ids = _top_ids("onde está a remessa 45871", catalog)
    assert "acme.shipments.tracking" in ids
    assert ids[0] == "acme.shipments.tracking"
    assert "acme.products.search" not in ids[:2]


def test_metamorphic_path_operation_rename_preserves_family_recall():
    base = _catalog()
    renamed = _metamorphic_catalog(base)
    # Map original expected family index → renamed actionId
    # product_search is index 0 in _catalog()
    message = "liste os top 50 terminais pino"
    ids = _top_ids(message, renamed)
    assert "vendor.renamed.0" in ids
    assert ids[0] == "vendor.renamed.0"

    stock_message = "qual o estoque do produto 10080047"
    stock_ids = _top_ids(stock_message, renamed)
    assert "vendor.renamed.1" in stock_ids


def test_catalog_has_no_registry_marker_fields():
    """Guard: harness must not smuggle pathMarkers into the catalog."""
    forbidden = {
        "pathMarkers",
        "operationIdMarkers",
        "excludePathMarkers",
        "routeSegment",
        "pathSuffix",
        "pathExactEnd",
        "parameterStrategy",
    }
    for row in _catalog():
        assert forbidden.isdisjoint(row.keys()), row
