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


def test_presenter_kpi_title_commercial_rol_target_not_generic():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()

    branch_title = presenter._kpi_title("/commercial/branch_rol_target_pct")
    head_title = presenter._kpi_title("/commercial/head_office_rol_target_pct")

    assert branch_title == "Meta % ROL comercial — filial"
    assert head_title == "Meta % ROL comercial — matriz"
    assert "Indicador Comercial" not in branch_title
    assert "Indicador Comercial" not in head_title


def test_title_for_path_prefers_longest_fragment():
    title = ChatAssistantContentService.title_for_path(
        "presenter_content",
        "/production/orders/open?branch=01",
    )

    assert title == "OPs em aberto"


def test_kpi_title_prefers_playbook_operational_path_over_generic_production():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()

    title = presenter._kpi_title("/production/work-centers/order-summary")

    assert title == "Resumo de OPs por centro de trabalho"
    assert "Indicador de Produção" not in title


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
    assert result.get("titulo") == "OPs em aberto"
    assert "Produto A" in "\n".join(result.get("linhas") or [])
    assert "Ordens de venda" not in str(result.get("titulo") or "")


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
    assert result.get("titulo") == "OPs em aberto"
    assert "Ordens de venda" not in str(result.get("titulo") or "")


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
