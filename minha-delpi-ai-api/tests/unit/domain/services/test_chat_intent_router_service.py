from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_intent_router_service import ChatIntentRouterService


def test_intent_router_content_bundles_have_router_terms():
    assert ChatAssistantContentService.list("intent_router", "selfHelpPhrases")
    assert ChatAssistantContentService.list(
        "product_query_intent",
        "router",
        "operationalKeywords",
    )


def test_classify_text_task_pure():
    route = ChatIntentRouterService.classify(
        "corrija: segue em anexo os documento solicitado",
        text_task_pure=True,
        text_task_category="correct",
    )

    assert route.intent == "text_task"
    assert route.sub_intent == "correct"
    assert route.requires_tool is False
    assert route.priority_applied == 3


def test_classify_conversation_meta_not_operational_with_memory_focus():
    route = ChatIntentRouterService.classify(
        "o que me diz sobre a conversa?",
        previous_messages=[
            {"role": "user", "content": "estoque 10080055"},
            {"role": "assistant", "content": "Saldo 26623"},
        ],
        workspace_context={
            "actionsEnabled": True,
            "allowedActionIds": ["action-1"],
            "workingMemory": {
                "operationalFocus": {
                    "productCode": "10080055",
                    "branch": "02",
                }
            },
        },
        allowed_action_ids=["action-1"],
    )

    assert route.intent == "session_review"
    assert route.requires_tool is False
    assert route.decision == "session_review"


def test_classify_filial_short_reply_stays_operational_with_memory():
    route = ChatIntentRouterService.classify(
        "filial 02",
        previous_messages=[
            {"role": "user", "content": "estoque 10080055"},
            {"role": "assistant", "content": "Saldo total"},
        ],
        workspace_context={
            "actionsEnabled": True,
            "allowedActionIds": ["action-1"],
            "workingMemory": {
                "operationalFocus": {"productCode": "10080055", "branch": "01"}
            },
        },
        allowed_action_ids=["action-1"],
    )

    assert route.intent == "operational_query"
    assert route.is_follow_up is True


def test_classify_operational_stock():
    route = ChatIntentRouterService.classify("qual o estoque do produto 10080001?")

    assert route.intent == "operational_query"
    assert route.sub_intent == "stock_lookup"
    assert route.requires_tool is False or route.requires_tool is True


def test_classify_saldo_disponivel_routes_to_stock_not_clarify():
    route = ChatIntentRouterService.classify(
        "Qual o saldo disponível do produto 10080033 na filial 01?",
        allowed_action_ids=["action-1"],
    )

    assert route.intent == "operational_query"
    assert route.sub_intent == "stock_lookup"
    assert route.ambiguous is False
    assert route.decision == "operational_action"
    assert route.resolved_params.get("productCode") == "10080033"


def test_classify_supplier_question_quem_fornece_not_ambiguous():
    route = ChatIntentRouterService.classify("quem fornece o produto 10080022?")

    assert route.intent == "operational_query"
    assert route.sub_intent == "supplier_lookup"
    assert route.ambiguous is False
    assert route.resolved_params == {"productCode": "10080022"}


def test_classify_billing_question_not_ambiguous():
    route = ChatIntentRouterService.classify(
        "Quanto já foi faturado do produto 90260015?",
        allowed_action_ids=["get_product_sales_billing"],
    )

    assert route.intent == "operational_query"
    assert route.sub_intent == "billing_lookup"
    assert route.ambiguous is False
    assert route.decision == "operational_action"
    assert route.resolved_params.get("productCode") == "90260015"


def test_classify_factory_status_question_not_ambiguous():
    route = ChatIntentRouterService.classify(
        "Qual o status completo na fábrica do produto 90269002 hoje?",
        allowed_action_ids=["get_product_factory_status"],
    )

    assert route.intent == "operational_query"
    assert route.sub_intent == "factory_status_lookup"
    assert route.ambiguous is False
    assert route.decision == "operational_action"
    assert route.resolved_params.get("productCode") == "90269002"


def test_classify_financial_rol_routes_to_department_kpi_not_self_help():
    route = ChatIntentRouterService.classify(
        "Qual foi o ROL da empresa em março de 2026?",
        allowed_action_ids=["get_rol_financial_rol_get"],
    )

    assert route.intent == "operational_query"
    assert route.sub_intent == "department_kpi"
    assert route.decision == "operational_action"
    assert route.reason == "department_kpi_keywords"


def test_classify_system_metadata_table_question():
    route = ChatIntentRouterService.classify(
        "qual a tabela de produtos?",
        allowed_action_ids=["api_delpi.system.search_tables_system_tables_search_get"],
    )

    assert route.intent == "operational_query"
    assert route.sub_intent == "system_metadata"


def test_classify_small_talk():
    route = ChatIntentRouterService.classify("obrigado!")

    assert route.intent == "small_talk"
    assert route.requires_llm is False


def test_resolve_executed_from_pipeline_stages():
    route = ChatIntentRouterService.resolve_executed(
        message="obrigado!",
        pipeline_stages=["ingress", "small_talk", "post_tool", "skip_rag", "direct_answer"],
        skip_rag=True,
        direct_answer="De nada!",
    )

    assert route.intent == "small_talk"
    assert "stage:small_talk" in route.flags


def test_resolve_executed_does_not_promote_no_clear_intent_without_tools():
    route = ChatIntentRouterService.resolve_executed(
        message="xyzzy-nonsense-token",
        pipeline_stages=["ingress", "tools", "post_tool", "skip_rag"],
        tool_calls=[],
        skip_rag=True,
    )

    assert route.intent == "llm_general"
    assert route.reason == "no_clear_intent"
    assert route.decision == "llm_fallback"
    assert "stage:tools" not in (route.flags or ())


def test_resolve_executed_tv_copilot_claims_oee_turn():
    route = ChatIntentRouterService.resolve_executed(
        message="adicione o modelo de dados oee",
        pipeline_stages=["ingress", "tools", "post_tool", "skip_rag"],
        workspace_context={
            "tvDashboardHostContext": {
                "surface": "tv-dashboard",
                "playlistId": "pl-1",
                "slideId": "sl-1",
            }
        },
        tool_calls=[
            {
                "name": "tv_dashboard_copilot",
                "arguments": {"mode": "apply"},
                "metadata": {"ok": True},
            }
        ],
        skip_rag=True,
        direct_answer="Alteração aplicada.",
    )

    assert route.intent == "platform_action"
    assert route.sub_intent == "tv_dashboard_copilot"
    assert route.decision == "platform_action"
    assert route.reason == "platform_tool_executed"
    assert "platform_tool_executed" in route.flags


def test_resolve_executed_drawing_analysis_beats_tools():
    route = ChatIntentRouterService.resolve_executed(
        message="analise o desenho 90260140",
        pipeline_stages=[
            "ingress",
            "tools",
            "drawing_analysis",
            "post_tool",
            "skip_rag",
            "direct_answer",
        ],
        skip_rag=True,
        direct_answer="# Relatório",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "path": "/products/90260140/analyser"},
            }
        ],
    )

    assert route.intent == "drawing_analysis"
    assert "stage:drawing_analysis" in route.flags


def test_resolve_executed_text_task_stage():
    route = ChatIntentRouterService.resolve_executed(
        message="resuma o texto abaixo",
        pipeline_stages=["ingress", "text_task", "post_tool", "skip_rag"],
        text_task_pure=True,
        text_task_category="summarize",
        skip_rag=True,
    )

    assert route.intent == "text_task"


def test_classify_operational_follow_up_resolves_product_from_memory():
    history = [
        {"role": "user", "content": "me fale do produto 10080001"},
        {
            "role": "assistant",
            "content": "Informações do produto.",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080001/analyser"},
                    }
                ]
            },
        },
    ]

    route = ChatIntentRouterService.classify(
        "e as vendas desse produto",
        previous_messages=history,
    )

    assert route.intent == "operational_query"
    assert route.is_follow_up is True
    assert route.resolved_params == {"productCode": "10080001"}
    assert route.to_dict().get("resolvedParams") == {"productCode": "10080001"}


def test_classify_operational_includes_product_code_in_resolved_params():
    route = ChatIntentRouterService.classify("qual o estoque do produto 10080001?")

    assert route.resolved_params == {"productCode": "10080001"}
    assert route.to_dict()["resolvedParams"]["productCode"] == "10080001"
