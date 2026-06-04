from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def test_loads_stream_activity_phase_groups():
    label = ChatAssistantContentService.get_mapping("stream", "activity", "phaseGroups").get(
        "tools"
    )

    assert label == "Consultando"


def test_product_overview_intent_terms_loaded():
    terms = ChatAssistantContentService.list(
        "product_overview_intent", "overviewTerms"
    )

    assert "me fale do produto" in terms


def test_presenter_route_presentations_guide():
    line = ChatAssistantContentService.format(
        "presenter_content",
        "routePresentations",
        "guide",
        "mainOps",
        code="90260114",
        count="3",
        preview="**10** Usinagem",
    )

    assert "90260114" in line
    assert "3" in line


def test_presenter_operational_empty_messages():
    message = ChatAssistantContentService.format(
        "presenter_content",
        "operationalEmpty",
        "stock",
        code="10080022",
    )

    assert "10080022" in message


def test_product_query_intent_stock_terms_loaded():
    terms = ChatAssistantContentService.list("product_query_intent", "stock", "terms")

    assert "estoque" in terms
    assert "saldo" in terms


def test_analyser_insights_attention_keys_exist():
    message = ChatAssistantContentService.get(
        "analyser_insights",
        "attention",
        "guideMissing",
    )

    assert "roteiro" in message.lower()


def test_presenter_kpi_title_from_path_matchers():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()

    assert "PMR" in presenter._kpi_title("/financial/pmr")
    assert "CPV" in presenter._kpi_title("/production/cpv")


def test_sql_error_maps_to_error_handling_message():
    summary = ChatAssistantContentService.get_error_type(
        "sql_syntax_error",
        "userMessage",
    )

    assert "sintaxe" in summary.lower()
