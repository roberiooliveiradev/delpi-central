from app.domain.services.chat_product_multi_scope_planning_service import (
    ChatProductMultiScopePlanningService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


class FakeScopeSelectionService:
    def select_action_for_product(
        self,
        message,
        *,
        product_code,
        allowed_action_ids=None,
        intent=None,
        route_segment=None,
        previous_messages=None,
    ):
        path = "/products/{code}/analyser"

        if intent == ChatProductQueryIntent.STRUCTURE:
            path = "/products/{code}/structure"
        elif route_segment == "guide":
            path = "/products/{code}/guide"
        elif route_segment == "inspection":
            path = "/products/{code}/inspection"
        elif intent == ChatProductQueryIntent.DESCRIPTION:
            path = "/products/{code}"
        elif intent == ChatProductQueryIntent.STOCK:
            path = "/products/{code}/stock"
        elif route_segment == "open-orders":
            path = "/products/{code}/sales/open-orders"
        elif route_segment == "stock":
            path = "/products/{code}/stock"
        elif route_segment == "analyser" or intent == ChatProductQueryIntent.ANALYSER:
            path = "/products/{code}/analyser"

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": f"action-{path}",
                "parameters": {"code": product_code},
                "path": path,
            },
        }


def test_extract_scopes_structure_and_guide():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "mostre estrutura e roteiro do produto 90260149",
    )

    assert scopes == ("guide", "structure")


def test_extract_scopes_stock_and_outbound_invoice():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "estoque e notas fiscais de saída do produto 90260148",
    )

    assert "stock" in scopes
    assert "outbound_invoice" in scopes


def test_generic_notas_fiscais_alone_not_in_multi_scope():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "notas fiscais e estoque do produto 90260148",
    )

    assert "stock" in scopes
    assert "inbound_invoice" not in scopes
    assert "outbound_invoice" not in scopes


def test_should_use_single_analyser_for_explicit_completa():
    scopes = ("guide", "structure")

    assert ChatProductMultiScopePlanningService.should_use_single_analyser(
        scopes,
        "informações completas do produto 90260149",
    )


def test_should_use_single_analyser_for_three_analyser_scopes():
    scopes = ("profile", "guide", "structure")

    assert ChatProductMultiScopePlanningService.should_use_single_analyser(
        scopes,
        "cadastro roteiro e estrutura do 90260149",
    )


def test_should_not_use_single_analyser_for_two_scopes_without_completa():
    scopes = ("guide", "structure")

    assert not ChatProductMultiScopePlanningService.should_use_single_analyser(
        scopes,
        "estrutura e roteiro do produto 90260149",
    )


def test_detect_multi_scope_intent():
    intent = ChatProductQueryIntentService.detect(
        "estrutura e roteiro do produto 90260149",
        force_legacy=True,
    )

    assert intent == ChatProductQueryIntent.MULTI_SCOPE


def test_extract_scopes_empty_for_purchase_price_history_playbook():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "Histórico de preço de compra do 10080001",
    )

    assert scopes == ()

    intent = ChatProductQueryIntentService.detect(
        "Histórico de preço de compra do 10080001",
    )

    assert intent != ChatProductQueryIntent.MULTI_SCOPE


def test_extract_scopes_empty_for_purchase_budget_history_playbook():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "Histórico de orçamento de compra do produto 10080001",
    )

    assert scopes == ()


def test_detect_analyser_for_integrated_three_scopes():
    intent = ChatProductQueryIntentService.detect(
        "análise integrada do cadastro, roteiro e estrutura do 90260149",
        force_legacy=True,
    )

    assert intent == ChatProductQueryIntent.ANALYSER


def test_plan_fetches_two_routes():
    service = FakeScopeSelectionService()

    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        service,
        message="estrutura e roteiro do produto 90260149",
        product_code="90260149",
        allowed_action_ids=["a1"],
    )

    assert len(planned) == 2
    paths = {
        str(item["arguments"].get("path") or "")
        for item in planned
    }

    assert "/products/{code}/structure" in paths
    assert "/products/{code}/guide" in paths


def test_plan_scope_select_uses_scoped_message_not_compound_utterance():
    """C4 — OpenAPI-first must not see stock+structure in the same select call."""
    seen: list[tuple[str, str | None]] = []

    class SpyService(FakeScopeSelectionService):
        def select_action_for_product(
            self,
            message,
            *,
            product_code,
            allowed_action_ids=None,
            intent=None,
            route_segment=None,
            previous_messages=None,
        ):
            seen.append((str(message), route_segment))
            return super().select_action_for_product(
                message,
                product_code=product_code,
                allowed_action_ids=allowed_action_ids,
                intent=intent,
                route_segment=route_segment,
                previous_messages=previous_messages,
            )

    compound = (
        "Agora completa: inclui também a estrutura e um comentário se o estoque "
        "cobre demanda típica."
    )
    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        SpyService(),
        message=compound,
        product_code="90260149",
        allowed_action_ids=["a1"],
    )

    assert planned
    assert all(compound not in msg for msg, _seg in seen)
    structure_calls = [msg for msg, seg in seen if seg == "structure"]
    stock_calls = [msg for msg, seg in seen if seg == "stock"]
    assert structure_calls
    assert stock_calls
    assert all("estoque" not in msg.lower() for msg in structure_calls)
    assert all("estrutura" not in msg.lower() for msg in stock_calls)


def test_plan_fetches_single_analyser_when_completa():
    service = FakeScopeSelectionService()

    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        service,
        message="informações completas do produto 90260149",
        product_code="90260149",
        allowed_action_ids=["a1"],
    )

    assert len(planned) == 1
    assert "/analyser" in str(planned[0]["arguments"].get("path") or "")


def test_plan_fetches_analyser_plus_stock_for_visao_integrada():
    service = FakeScopeSelectionService()

    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        service,
        message="visão integrada e estoque do produto 90260149",
        product_code="90260149",
        allowed_action_ids=["a1"],
    )

    assert len(planned) >= 2
    paths = {str(item["arguments"].get("path") or "") for item in planned}
    assert any("/analyser" in path for path in paths)
    assert any("/stock" in path for path in paths)


def test_plan_fetches_expands_bundle_when_analyser_action_missing():
    class NoAnalyserService(FakeScopeSelectionService):
        def select_action_for_product(
            self,
            message,
            *,
            product_code,
            allowed_action_ids=None,
            intent=None,
            route_segment=None,
            previous_messages=None,
        ):
            if intent == ChatProductQueryIntent.ANALYSER:
                return None
            return super().select_action_for_product(
                message,
                product_code=product_code,
                allowed_action_ids=allowed_action_ids,
                intent=intent,
                route_segment=route_segment,
                previous_messages=previous_messages,
            )

    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        NoAnalyserService(),
        message=(
            "visão integrada do produto 90260149: ficha, estrutura, roteiro e estoque"
        ),
        product_code="90260149",
        allowed_action_ids=["a1"],
    )

    paths = {str(item["arguments"].get("path") or "") for item in planned}
    assert any("/stock" in path for path in paths)
    assert any(
        marker in path
        for path in paths
        for marker in ("/structure", "/guide", "/products/{code}")
    )
    assert len(planned) >= 2


def test_blocks_fast_path_when_visao_integrada_has_stock_companion():
    assert ChatProductMultiScopePlanningService.blocks_intent_bound_fast_path(
        "visão integrada e estoque do produto 90260149",
    )
    assert not ChatProductMultiScopePlanningService.blocks_intent_bound_fast_path(
        "informações completas do produto 90260149",
    )
    assert not ChatProductMultiScopePlanningService.blocks_intent_bound_fast_path(
        "estoque do produto 90260149",
    )


def test_extract_scopes_includes_open_orders():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "estrutura, estoque e pedidos em aberto do produto 90260149",
    )

    assert "structure" in scopes
    assert "stock" in scopes
    assert "open_orders" in scopes


def test_exclusive_sale_orders_list_turn():
    assert ChatProductMultiScopePlanningService.is_exclusive_open_orders_or_sale_orders_list_turn(
        "pedidos em aberto do produto 10080047",
    )
    assert not ChatProductMultiScopePlanningService.is_exclusive_open_orders_or_sale_orders_list_turn(
        "estrutura, estoque e pedidos em aberto do produto 90260149",
    )


def test_missing_scopes_for_planned_actions_detects_structure_gap():
    planned = [
        {
            "arguments": {
                "path": "/products/{code}/stock",
                "parameters": {"code": "90260149"},
            }
        }
    ]
    missing = ChatProductMultiScopePlanningService.missing_scopes_for_planned_actions(
        "inclui também a estrutura e o estoque do produto",
        planned,
    )
    assert "structure" in missing
    assert "stock" not in missing


def test_missing_scopes_accepts_openapi_action_id_without_path():
    planned = [
        {
            "name": "execute_external_action",
            "arguments": {"actionId": "structure", "parameters": {"code": "90260149"}},
            "metadata": {"actionId": "structure", "path": "/products/{code}/structure"},
        },
        {
            "name": "execute_external_action",
            "arguments": {"actionId": "guide", "parameters": {"code": "90260149"}},
            "metadata": {"actionId": "guide", "path": "/products/{code}/guide"},
        },
    ]
    missing = ChatProductMultiScopePlanningService.missing_scopes_for_planned_actions(
        "para o produto 90260149 traga (1) a estrutura BOM e (2) o roteiro de fabricação",
        planned,
    )
    assert missing == ()


def test_se_disponivel_alone_does_not_add_stock_scope():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "mostre o KPI e a série no tempo em gráfico se disponível",
    )

    assert "stock" not in scopes


def test_estoque_still_adds_stock_scope():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "saldo de estoque do produto 90260149",
    )

    assert "stock" in scopes


def test_extract_scopes_stock_and_description():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "estoque e descrição do produto 90260149",
    )

    assert "stock" in scopes
    assert "profile" in scopes


def test_summary_path_covers_profile_but_not_stock():
    missing = ChatProductMultiScopePlanningService.missing_scopes_for_planned_actions(
        "estoque e descrição do produto 90260149",
        [
            {
                "arguments": {"path": "/products/90260149/summary"},
            }
        ],
    )

    assert "stock" in missing
    assert "profile" not in missing


def test_extract_scopes_stock_only_consulta_estoque():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "Consulte o estoque do produto 10080001",
    )
    assert scopes == ("stock",)


def test_extract_scopes_nao_inspecao_does_not_add_inspection():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "Consulte o estoque do produto 10080001 via ferramenta de estoque/saldo "
        "(não inspeção). Mostre em tabela."
    )
    assert "stock" in scopes
    assert "inspection" not in scopes


def test_extract_scopes_sem_inspecao_does_not_add_inspection():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "saldo disponível do produto 10080001 sem inspeção",
    )
    assert "stock" in scopes
    assert "inspection" not in scopes


def test_extract_scopes_positive_inspecao_keeps_inspection():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "inspeção do produto 10080001",
    )
    assert scopes == ("inspection",)


def test_plan_fetches_single_stock_scope():
    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        FakeScopeSelectionService(),
        message="Consulte o estoque do produto 10080001",
        product_code="10080001",
        allowed_action_ids=["a1"],
    )
    paths = {str(item["arguments"].get("path") or "") for item in planned}
    assert paths == {"/products/{code}/stock"}
