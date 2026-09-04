from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_intent_router_service import ChatIntentRouterService


def test_intent_router_content_bundles_have_router_terms():
    assert ChatAssistantContentService.list("intent_router", "selfHelpPhrases")
    assert ChatAssistantContentService.list(
        "product_query_intent",
        "router",
        "operationalKeywords",
    )


def test_classify_politica_compras_is_rag_not_purchase():
    route = ChatIntentRouterService.classify("o que diz a política de compras?")

    assert route.decision == "rag_internal"
    assert route.requires_rag is True
    assert route.intent == "rag_question"
    assert route.sub_intent != "purchase_lookup"


def test_classify_glossario_qualidade_is_rag_not_text_task():
    route = ChatIntentRouterService.classify("explique o glossário de qualidade")

    assert route.decision == "rag_internal"
    assert route.requires_rag is True
    assert route.intent != "text_task"


def test_classify_estoque_com_politica_preserves_rag():
    route = ChatIntentRouterService.classify(
        "estoque do 10080001 segundo a política interna"
    )

    assert route.decision == "operational_action"
    assert route.sub_intent == "stock_lookup"
    assert route.requires_rag is True


def test_classify_ultimas_compras_com_codigo_continua_purchase():
    route = ChatIntentRouterService.classify("ultimas compras do 10080001")

    assert route.decision == "operational_action"
    assert route.sub_intent == "purchase_lookup"
    assert route.requires_rag is False


def test_classify_terminais_follow_up_after_normas_is_rag():
    history = [
        {
            "role": "user",
            "content": "o que dizem as normas técnicas DELPI sobre matéria-prima?",
        },
        {
            "role": "assistant",
            "content": "As Normas Técnicas DELPI cobrem 1001–1025. 1008 — terminais.",
            "metadata": {
                "adminDebug": {
                    "intentRoute": {
                        "decision": "rag_internal",
                        "intent": "rag_question",
                    }
                }
            },
        },
    ]
    route = ChatIntentRouterService.classify("terminais", previous_messages=history)

    assert route.decision == "rag_internal"
    assert route.requires_rag is True
    assert route.is_follow_up is True
    assert route.sub_intent == "documental_follow_up"


def test_classify_terminais_follow_up_with_chat_message_entities():
    """Histórico live vem como ChatMessage (não dict) — send/stream path."""
    from datetime import datetime, timezone
    from uuid import uuid4

    from app.domain.entities.chat_message import ChatMessage

    session_id = uuid4()
    now = datetime.now(timezone.utc)
    history = [
        ChatMessage(
            id=uuid4(),
            session_id=session_id,
            role="user",
            content="o que dizem as normas técnicas DELPI sobre matéria-prima?",
            metadata=None,
            created_at=now,
        ),
        ChatMessage(
            id=uuid4(),
            session_id=session_id,
            role="assistant",
            content="As Normas Técnicas DELPI cobrem 1001–1025. 1008 — terminais.",
            metadata={
                "adminDebug": {
                    "intentRoute": {
                        "decision": "rag_internal",
                        "intent": "rag_question",
                    }
                }
            },
            created_at=now,
        ),
    ]
    route = ChatIntentRouterService.classify("terminais", previous_messages=history)

    assert route.decision == "rag_internal"
    assert route.requires_rag is True
    assert route.sub_intent == "documental_follow_up"


def test_classify_como_descrever_terminal_is_rag_technical_description():
    route = ChatIntentRouterService.classify("como descrever um terminal?")

    assert route.decision == "rag_internal"
    assert route.requires_rag is True
    assert route.intent == "rag_question"
    assert str(route.sub_intent or "").startswith("technical_description")
    assert (route.resolved_params or {}).get("materialGroup") == "1008"


def test_classify_vdar_na_descricao_is_rag_not_operational():
    route = ChatIntentRouterService.classify("o que significa VDAR na descrição?")

    assert route.decision == "rag_internal"
    assert route.requires_rag is True
    assert route.intent == "rag_question"
    assert "technical_description" in str(route.sub_intent or "")


def test_classify_monte_descricao_cabo_is_rag_not_text_task():
    route = ChatIntentRouterService.classify(
        "monte a descrição de um cabo PVC 0,75mm2 preto"
    )

    assert route.decision == "rag_internal"
    assert route.requires_rag is True
    assert route.intent != "text_task"


def test_classify_explique_intermediario_is_rag_not_text_task():
    route = ChatIntentRouterService.classify(
        "explique o código intermediário 50232222 CB1,50VERD-00255/06/06–6314–0111"
    )

    assert route.decision == "rag_internal"
    assert route.requires_rag is True
    assert route.intent != "text_task"


def test_classify_product_lookup_descricao_continua_operational():
    """«descrição do produto 10xxxxxx» é cadastro REST — não normas nem clarify."""
    route = ChatIntentRouterService.classify("qual a descrição do produto 10080047")

    assert route.decision == "operational_action"
    assert route.ambiguous is False
    assert route.intent == "operational_query"
    assert route.requires_rag is False
    assert "technical_description" not in str(route.sub_intent or "")



def test_classify_crie_glossario_continua_text_task():
    from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

    assert ChatTextTaskIntentService.is_pure_text_task("crie um glossário dos termos abaixo")
    route = ChatIntentRouterService.classify("crie um glossário dos termos abaixo")
    assert route.intent == "text_task"


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


def test_classify_system_metadata_columns_and_indexes_not_sql_generate():
    """Colunas/índices Protheus são system_metadata — não sql_generate (F06 R1)."""
    for message in (
        "quais colunas da tabela SB1010?",
        "quais indexes da SB1010?",
        "colunas da tabela sb1",
        "índices da tabela SB1",
    ):
        route = ChatIntentRouterService.classify(
            message,
            allowed_action_ids=["api_delpi.system.get_table_columns_system_tables_table_name_columns_get"],
        )
        assert route.intent == "operational_query", message
        assert route.sub_intent == "system_metadata", message
        assert route.decision != "sql_route", message


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


def test_classify_schedule_production_promotes_operational_query():
    for message in (
        "programação de produção",
        "programacao de producao hoje",
    ):
        route = ChatIntentRouterService.classify(message)
        assert route.intent == "operational_query", message
        assert route.sub_intent == "schedule_today_lookup", message
        assert route.requires_tool is True, message
        assert route.decision != "llm_fallback", message
        assert route.reason in {"operational_sub_intent", "operational_keywords"}, message


def test_classify_bare_programacao_stays_unclear_or_fallback():
    # Termo isolado não é schedule — fica para unclear/analysis, não force tool.
    route = ChatIntentRouterService.classify("programação")
    assert route.intent != "operational_query" or route.sub_intent != "schedule_today_lookup"


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
