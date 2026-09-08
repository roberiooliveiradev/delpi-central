"""Aceite OpenAPI-first — operations próximas, compound e multi-turn (§28)."""

from __future__ import annotations

from app.application.services.decompose_external_action_requests_service import (
    DecomposeExternalActionRequestsService,
)
from app.application.services.openapi_first_selection_bridge_service import (
    OpenApiFirstSelectionBridgeService,
)
from app.application.services.plan_external_actions_service import (
    PlanExternalActionsService,
)
from app.domain.services.openapi_planner_mode_service import OpenApiPlannerModeDecision
from app.infrastructure.config.settings import Settings


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


def _mode_on() -> OpenApiPlannerModeDecision:
    return OpenApiPlannerModeDecision(
        mode="on",
        use_openapi_selection=True,
        run_shadow_compare=False,
        canary_matched=False,
    )


def _action(
    action_id: str,
    path: str,
    operation_id: str,
    *,
    summary: str,
    description: str = "",
    method: str = "GET",
) -> dict:
    return {
        "actionId": action_id,
        "providerKey": "acme",
        "method": method,
        "path": path,
        "operationId": operation_id,
        "summary": summary,
        "description": description or summary,
        "enabled": True,
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}},
        ],
        "sensitivity": "read",
    }


SIMILAR_COMPONENT_ACTIONS = [
    _action(
        "get_component_cost",
        "/components/{code}/cost",
        "get_component_cost",
        summary="Current component cost",
        description="Return the latest unit cost for a component",
    ),
    _action(
        "get_component_cost_history",
        "/components/{code}/cost/history",
        "get_component_cost_history",
        summary="Component cost history",
        description="Historical cost series for a component over time",
    ),
    _action(
        "export_component_cost_history",
        "/components/{code}/cost/history/export",
        "export_component_cost_history",
        summary="Export component cost history spreadsheet",
        description="Download Excel/CSV export of component cost history",
    ),
]


STRUCTURE_ACTIONS = [
    _action(
        "structure-excel",
        "/products/{code}/structure/excel",
        "get_product_structure_excel",
        summary="Export product structure as Excel spreadsheet",
        description="Generate/download BOM structure planilha Excel export",
    ),
    _action(
        "structure",
        "/products/{code}/structure",
        "get_product_structure",
        summary="Estrutura (BOM) do produto",
        description=(
            "Lista a estrutura / lista de materiais (BOM). Use para árvore de componentes "
            "sem exclusividade de matérias-primas."
        ),
    ),
    _action(
        "structure-exclusivity",
        "/products/{code}/structure/exclusivity",
        "get_product_structure_exclusivity",
        summary="Exclusividade de matérias-primas na estrutura",
        description=(
            "Use SOMENTE quando o usuário pedir exclusividade ou MP exclusiva. "
            "Para BOM comum use /structure."
        ),
    ),
]


PRODUCT_VIEW_ACTIONS = [
    _action(
        "summary",
        "/products/{code}/summary",
        "get_product_summary",
        summary="Resumo leve do produto (cadastro + amostra de estoque + preços)",
        description=(
            "Use somente para visão geral rápida quando NÃO pediu BOM, roteiro, "
            "analisador completo nem visão integrada."
        ),
    ),
    _action(
        "analyser",
        "/products/{code}/analyser",
        "get_product_analyser",
        summary="Analisador completo / visão integrada do produto",
        description=(
            "Consolida cadastro, estrutura, roteiro e inspeção. Use para visão integrada, "
            "ficha completa ou cadastro + estrutura + roteiro juntos."
        ),
    ),
    _action(
        "stock",
        "/products/{code}/stock",
        "get_product_stock",
        summary="Estoque do produto",
        description="Saldo e posições de estoque do produto",
    ),
    _action(
        "structure",
        "/products/{code}/structure",
        "get_product_structure",
        summary="Estrutura (BOM) do produto",
        description="BOM / árvore de componentes sem exclusividade",
    ),
]


PURCHASE_ACTIONS = [
    _action(
        "last-purchase",
        "/products/{code}/last-purchase",
        "get_product_last_purchase",
        summary="Last purchase and ICMS of the product",
        description="Última compra e ICMS do produto",
    ),
    _action(
        "purchases",
        "/products/{code}/purchases",
        "get_product_purchases",
        summary="Product purchases list",
        description="Lista de compras do produto",
    ),
    _action(
        "purchase-budget-history",
        "/products/{code}/purchase-budget-history",
        "get_product_purchase_budget_history",
        summary="Purchase budget history",
        description="Histórico de orçamento de compra do produto",
    ),
    _action(
        "raw-material-price-intelligence",
        "/products/{code}/raw-material-price-intelligence",
        "get_raw_material_price_intelligence",
        summary="Raw material price intelligence analysis",
        description="Análise de preço da matéria-prima",
    ),
    _action(
        "pricing",
        "/products/{code}/pricing",
        "get_product_pricing",
        summary="Product pricing",
        description="Preço comercial do produto",
    ),
]


def _plan(message: str, actions: list[dict]):
    repo = _CatalogRepository(actions)
    bridge = OpenApiFirstSelectionBridgeService(repo, planner=PlanExternalActionsService(llm_planner=None))
    allowed = [str(item["actionId"]) for item in actions]
    return bridge.plan_tool_calls(
        message,
        allowed_action_ids=allowed,
        catalog_actions=actions,
        mode_decision=_mode_on(),
    )


def _first_action_id(planned: list[dict]) -> str:
    assert planned, "expected planned tools"
    first = planned[0]
    args = first.get("arguments") or {}
    return str(args.get("actionId") or first.get("actionId") or "")


def test_similar_ops_prefers_current_cost_over_history():
    planned = _plan("qual o custo atual do componente X123", SIMILAR_COMPONENT_ACTIONS)
    assert _first_action_id(planned) == "get_component_cost"


def test_similar_ops_prefers_history_over_current():
    planned = _plan(
        "mostre o histórico do custo do componente X123",
        SIMILAR_COMPONENT_ACTIONS,
    )
    assert _first_action_id(planned) == "get_component_cost_history"


def test_similar_ops_prefers_export_spreadsheet():
    planned = _plan(
        "exporte o histórico de custo do componente X123 em excel",
        SIMILAR_COMPONENT_ACTIONS,
    )
    assert _first_action_id(planned) == "export_component_cost_history"


def test_structure_excel_beats_structure():
    planned = _plan("baixar estrutura em excel do produto 90261757", STRUCTURE_ACTIONS)
    assert _first_action_id(planned) == "structure-excel"


def test_structure_excel_planilha_bom():
    planned = _plan("exportar planilha BOM do 90261757", STRUCTURE_ACTIONS)
    assert _first_action_id(planned) == "structure-excel"


def test_last_purchase_beats_purchases():
    planned = _plan(
        "Última compra e ICMS do produto 10080001",
        PURCHASE_ACTIONS,
    )
    assert _first_action_id(planned) == "last-purchase"


def test_purchase_budget_history_beats_purchases():
    planned = _plan(
        "Histórico de orçamento de compra do produto 10080001",
        PURCHASE_ACTIONS,
    )
    assert _first_action_id(planned) == "purchase-budget-history"


def test_raw_material_price_beats_pricing():
    planned = _plan(
        "Análise de preço da matéria-prima 10080001",
        PURCHASE_ACTIONS,
    )
    assert _first_action_id(planned) == "raw-material-price-intelligence"


def test_compound_decomposes_into_multiple_subtasks():
    message = (
        "Veja a última compra do 10080001, compare com o preço atual, "
        "mostre o histórico de orçamento"
    )
    subtasks = DecomposeExternalActionRequestsService.decompose(message)
    assert len(subtasks) >= 2


def test_numbered_list_decomposes_into_multiple_subtasks():
    message = (
        "Para o produto 90260149, traga numa resposta só: (1) estrutura de bom, "
        "(2) saldo de estoque atual e (3) pedidos em aberto."
    )
    subtasks = DecomposeExternalActionRequestsService.decompose(message)
    assert len(subtasks) >= 2
    assert any("estrutura" in item.text.lower() for item in subtasks)
    assert any("estoque" in item.text.lower() for item in subtasks)


def test_compound_signal_wants_multi_action_without_joiner():
    message = (
        "Me dá uma visão integrada do produto 90260149: ficha, estrutura e estoque."
    )
    assert DecomposeExternalActionRequestsService.wants_multi_action(message)
    assert len(DecomposeExternalActionRequestsService.decompose(message)) == 1


def test_presentation_compound_signal_does_not_force_multi_action():
    message = (
        "Mostre o ROL comercial do mês em KPI e série, tudo na mesma resposta."
    )
    assert not DecomposeExternalActionRequestsService.wants_multi_action(message)
    assert len(DecomposeExternalActionRequestsService.decompose(message)) == 1


def test_small_talk_does_not_want_multi_action():
    assert not DecomposeExternalActionRequestsService.wants_multi_action("oi")


def test_integrated_view_prefers_analyser_over_summary():
    planned = _plan(
        "Me dá uma visão integrada do produto 90260149: ficha, estrutura e roteiro.",
        PRODUCT_VIEW_ACTIONS,
    )
    assert _first_action_id(planned) == "analyser"


def test_plain_structure_prefers_bom_not_exclusivity():
    planned = _plan(
        "traga a estrutura de bom/componentes do produto 90260149",
        STRUCTURE_ACTIONS,
    )
    assert _first_action_id(planned) == "structure"


def test_compound_plans_multiple_distinct_actions():
    message = (
        "Veja a última compra do 10080001 e tambem mostre o histórico de orçamento"
    )
    planned = _plan(message, PURCHASE_ACTIONS)
    action_ids = [
        str((item.get("arguments") or {}).get("actionId") or "")
        for item in planned
        if str(item.get("name") or "") == "execute_external_action"
    ]
    assert "last-purchase" in action_ids
    assert "purchase-budget-history" in action_ids


def test_multi_turn_prefers_previous_action_id_without_path_fragment():
    actions = STRUCTURE_ACTIONS
    repo = _CatalogRepository(actions)
    bridge = OpenApiFirstSelectionBridgeService(repo, planner=PlanExternalActionsService(llm_planner=None))
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "structure",
                            "parameters": {"code": "90261757"},
                        },
                        "metadata": {
                            "ok": True,
                            "actionId": "structure",
                            "path": "/products/90261757/structure",
                            "executionContext": {
                                "actionId": "structure",
                                "parameters": {"code": "90261757"},
                            },
                        },
                    }
                ]
            },
        }
    ]
    planned = bridge.plan_tool_calls(
        "agora em excel",
        allowed_action_ids=[item["actionId"] for item in actions],
        catalog_actions=actions,
        previous_messages=previous,
        mode_decision=_mode_on(),
    )
    # Follow-up mentioning excel must still pick excel (specificity > continuity alone).
    assert _first_action_id(planned) == "structure-excel"


def test_openapi_default_mode_is_on():
    assert Settings.CHAT_OPENAPI_PLANNER_MODE == "on"
