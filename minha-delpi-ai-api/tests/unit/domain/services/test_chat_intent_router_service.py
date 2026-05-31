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
