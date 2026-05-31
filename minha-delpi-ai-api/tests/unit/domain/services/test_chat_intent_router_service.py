from app.domain.services.chat_intent_router_service import ChatIntentRouterService


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


def test_classify_operational_stock():
    route = ChatIntentRouterService.classify("qual o estoque do produto 10080001?")

    assert route.intent == "operational_query"
    assert route.sub_intent == "stock_lookup"
    assert route.requires_tool is False or route.requires_tool is True


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
