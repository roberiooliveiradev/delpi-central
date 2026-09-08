"""Orquestração de actions sob OpenAPI-first fail-closed (sem FakeSelection/registry)."""

from __future__ import annotations

import pytest

from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)
from app.application.services.openapi_first_selection_bridge_service import (
    OpenApiFirstSelectionBridgeService,
)
from app.application.services.plan_external_actions_service import (
    PlanExternalActionsService,
)


@pytest.fixture(autouse=True)
def _deterministic_openapi_planner(monkeypatch):
    """Unit tests must not call the live LLM planner adapter."""
    real_init = OpenApiFirstSelectionBridgeService.__init__

    def _init(
        self,
        repository=None,
        *,
        semantic_ranker=None,
        planner=None,
        validator=None,
    ):
        real_init(
            self,
            repository,
            semantic_ranker=semantic_ranker,
            planner=planner or PlanExternalActionsService(llm_planner=None),
            validator=validator,
        )

    monkeypatch.setattr(OpenApiFirstSelectionBridgeService, "__init__", _init)


class _CatalogRepository:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        rows = [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ]
        return rows[:limit]

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []


class _Selection:
    def __init__(self, repo: _CatalogRepository):
        self.repository = repo
        self.semantic_ranker = None


def _action(
    action_id: str,
    path: str,
    operation_id: str,
    *,
    summary: str,
    description: str = "",
    extra_params: list[dict] | None = None,
) -> dict:
    params = [
        {
            "name": "code",
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
        },
        *(extra_params or []),
    ]
    return {
        "actionId": action_id,
        "providerKey": "api-delpi-fixture",
        "method": "GET",
        "path": path,
        "operationId": operation_id,
        "summary": summary,
        "description": description or summary,
        "enabled": True,
        "parametersSchema": params,
        "sensitivity": "read",
    }


PRODUCT_CATALOG = [
    _action(
        "stock",
        "/products/{code}/stock",
        "get_product_stock",
        summary="Estoque do produto",
        description="Saldo e posições de estoque do produto",
    ),
    _action(
        "product-detail",
        "/products/{code}",
        "get_product_detail",
        summary="Descrição e cadastro do produto",
        description="Detalhe descritivo / ficha cadastral do produto",
    ),
    _action(
        "structure",
        "/products/{code}/structure",
        "get_product_structure",
        summary="Estrutura BOM do produto",
        description="Árvore de componentes / lista de materiais (BOM)",
    ),
    _action(
        "guide",
        "/products/{code}/guide",
        "get_product_guide",
        summary="Roteiro de fabricação do produto",
        description="Guide / roteiro de operações de manufatura",
    ),
    _action(
        "parents",
        "/products/{code}/parents",
        "get_product_parents",
        summary="Onde o produto é usado / produtos pai",
        description="Produtos pais que usam o componente",
        extra_params=[
            {"name": "page", "in": "query", "schema": {"type": "integer"}},
            {"name": "page_size", "in": "query", "schema": {"type": "integer"}},
        ],
    ),
    _action(
        "open-orders",
        "/products/{code}/sales/open-orders",
        "get_product_open_orders",
        summary="Pedidos em aberto do produto",
        description="Pedidos de venda abertos para o código",
    ),
]


def _plan(message: str, actions: list[dict] | None = None, **kwargs):
    catalog = actions if actions is not None else PRODUCT_CATALOG
    repo = _CatalogRepository(catalog)
    return ChatExternalActionOrchestrationService.plan_actions(
        _Selection(repo),
        message=message,
        allowed_action_ids=[str(item["actionId"]) for item in catalog],
        workspace_context={
            "providerKeys": ["api-delpi-fixture"],
            **(kwargs.pop("workspace_context", None) or {}),
        },
        **kwargs,
    )


def _execute_ids(planned: list[dict]) -> set[str]:
    return {
        str((item.get("arguments") or {}).get("actionId") or "")
        for item in planned
        if item.get("name") == "execute_external_action"
    }


def _first_execute(planned: list[dict]) -> dict:
    for item in planned:
        if item.get("name") == "execute_external_action":
            return item
    raise AssertionError(f"expected execute_external_action, got {planned!r}")


def test_plan_actions_empty_plan_clarifies_openapi_first():
    planned = _plan("oi tudo bem")
    assert planned
    assert planned[0]["name"] == "clarify_external_action"
    metadata = planned[0].get("metadata") or {}
    assert metadata.get("selectionMode") == "openapi_first"
    assert metadata.get("emptyPlan") is True


def test_plan_actions_single_code_stock_openapi_first():
    planned = _plan("estoque do produto 10080047")
    first = _first_execute(planned)
    assert (first.get("metadata") or {}).get("selectionMode") == "openapi_first"
    assert first["arguments"]["actionId"] == "stock"
    assert first["arguments"]["parameters"]["code"] == "10080047"


def test_plan_actions_description_intent_openapi_first():
    planned = _plan("descrição do produto 90260149")
    first = _first_execute(planned)
    assert first["arguments"]["actionId"] == "product-detail"
    assert first["arguments"]["parameters"]["code"] == "90260149"


def test_plan_actions_prefers_message_code_over_history_noise():
    planned = _plan(
        "estoque do produto 10080047",
        previous_messages=[
            {
                "role": "assistant",
                "content": "Antes falamos do 99999999",
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "stock",
                            "parameters": {"code": "99999999"},
                        },
                    }
                ],
            }
        ],
    )
    first = _first_execute(planned)
    assert first["arguments"]["parameters"]["code"] == "10080047"


def test_plan_actions_compound_structure_and_guide():
    planned = _plan(
        "para o produto 90260149 traga (1) a estrutura BOM e (2) o roteiro de fabricação"
    )
    ids = _execute_ids(planned)
    assert {"structure", "guide"} <= ids
    for item in planned:
        if item.get("name") == "execute_external_action":
            assert (item.get("metadata") or {}).get("selectionMode") == "openapi_first"
            assert (item.get("arguments") or {}).get("parameters", {}).get("code") == "90260149"


def test_plan_actions_compound_structure_stock_open_orders():
    planned = _plan(
        "produto 90260149: (1) estrutura, (2) estoque e (3) pedidos em aberto"
    )
    ids = _execute_ids(planned)
    assert len(ids) >= 2
    assert "structure" in ids or "stock" in ids or "open-orders" in ids


def test_plan_actions_fast_mode_caps_multi_action(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_external_action_orchestration_service.Settings.CHAT_MULTI_ACTION_ENABLED",
        True,
    )
    planned = _plan(
        "para o produto 90260149 traga (1) a estrutura BOM e (2) o roteiro de fabricação",
        max_calls=1,
    )
    executes = [item for item in planned if item.get("name") == "execute_external_action"]
    assert len(executes) == 1
    assert executes[0]["arguments"]["actionId"] in {"structure", "guide"}


def test_plan_actions_followup_binds_code_from_previous_tool_call():
    planned = _plan(
        "quero também o estoque",
        previous_messages=[
            {
                "role": "assistant",
                "content": "Segue a estrutura do 90260149",
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "structure",
                            "parameters": {"code": "90260149"},
                        },
                        "metadata": {
                            "executionContext": {
                                "actionId": "structure",
                                "parameters": {"code": "90260149"},
                            }
                        },
                    }
                ],
            }
        ],
    )
    first = _first_execute(planned)
    assert first["arguments"]["actionId"] == "stock"
    assert first["arguments"]["parameters"]["code"] == "90260149"


def test_plan_actions_irrelevant_catalog_stays_fail_closed():
    foreign = [
        _action(
            "other-tracking",
            "/tracking/{code}",
            "get_tracking",
            summary="Tracking de remessa logística",
            description="Rastreio de shipment / remessa",
        )
    ]
    planned = _plan("estoque do produto 10080047", actions=foreign)
    assert planned[0]["name"] == "clarify_external_action"
    assert (planned[0].get("metadata") or {}).get("selectionMode") == "openapi_first"
