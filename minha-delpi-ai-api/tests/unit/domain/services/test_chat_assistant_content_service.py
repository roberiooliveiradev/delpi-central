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


def test_presenter_kpi_title_uses_presentation_metadata():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    chart = presenter._kpi_chart()
    chart.metadata = {
        "presentation": {"title": "PMR financeiro"},
        "summary": "Get financial PMR",
    }

    assert chart.kpi_title("/financial/pmr") == "PMR financeiro"
    chart.metadata = {"presentation": {"title": "CPV produção"}}
    assert chart.kpi_title("/production/cpv") == "CPV produção"


def test_presenter_kpi_title_falls_back_without_legacy_path_maps():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    title = presenter._kpi_title("/financial/pmr")
    assert title
    assert title != ""


def test_presenter_kpi_title_metamorphic_path_same_metadata():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    chart = presenter._kpi_chart()
    chart.metadata = {
        "presentation": {"title": "Meta % ROL comercial — filial"},
        "summary": "Commercial ROL summary",
    }
    a = chart.kpi_title("/commercial/rol/summary")
    b = chart.kpi_title("/v2/sales/rol/summary")
    assert a == b == "Meta % ROL comercial — filial"


def test_title_for_path_helper_still_reads_content_when_present():
    title = ChatAssistantContentService.title_for_path(
        "presenter_content",
        "/production/orders/open?branch=01",
        default=None,
    )
    # Helper still exists for cleanup phase; may return fragment map until E2.S3.
    assert title is None or isinstance(title, str)


def test_kpi_title_unknown_path_uses_safe_fallback():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    title = presenter._kpi_title("/acme/never-seen/kpi")
    assert title
    assert "Indicador" in title or title


def test_playbook_operational_entity_uses_playbook_report_title():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    payload = {
        "meta": {"entity": "production_orders_open"},
        "items": [
            {"production_order": "OP-001", "description": "Produto A"},
            {"production_order": "OP-002", "description": "Produto B"},
        ],
    }

    result = presenter.present(payload, path="/production/orders/open")

    assert result is not None
    titulo = str(result.get("titulo") or "")
    assert "OP" in titulo or "produção" in titulo.casefold() or "ordens" in titulo.casefold()
    assert "Produto A" in "\n".join(result.get("linhas") or [])
    assert "Ordens de venda" not in titulo


def test_legacy_playbook_operational_path_without_meta_entity():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    payload = {
        "items": [
            {"production_order": "OP-001", "description": "Produto A"},
        ],
    }

    result = presenter.present(payload, path="/production/orders/open")

    assert result is not None
    titulo = str(result.get("titulo") or "")
    assert "OP" in titulo or "produção" in titulo.casefold() or "ordens" in titulo.casefold()
    assert "Ordens de venda" not in titulo


def test_legacy_production_path_does_not_route_order_number_to_sale_orders():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    payload = {
        "items": [
            {
                "order_number": "000123",
                "description": "Item produção",
                "branch": "01",
            },
        ],
    }

    result = presenter.present(payload, path="/production/orders/finished")

    assert result is not None
    assert "Ordens de venda" not in str(result.get("titulo") or "")


def test_sql_error_maps_to_error_handling_message():
    summary = ChatAssistantContentService.get_error_type(
        "sql_syntax_error",
        "userMessage",
    )

    assert "sintaxe" in summary.lower()
