"""Texto e decisão operacional por perfil — Playbook 12 R5."""

from __future__ import annotations

from app.domain.services.chat_presentation_operational_decision_service import (
    ChatPresentationOperationalDecisionService,
)
from app.domain.services.chat_presentation_profile_text_builder_service import (
    ChatPresentationProfileTextBuilderService,
)
from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_pricing_intent_without_path_uses_vocabulary_markers():
    decision = ChatPresentationDecisionService.decide(
        intent="price_lookup",
        user_message="consulta comercial",
        text_presentation={"type": "markdown", "title": "Preços", "markdown": "Resumo"},
        table_presentation={
            "type": "table",
            "title": "Preços",
            "columns": [{"key": "sale_price", "label": "Preço"}],
            "rows": [{"sale_price": 10}],
        },
        rows=[{"sale_price": 10}],
    )

    assert decision["selected"] == "text"


def test_structure_intent_without_path_prefers_tree():
    tree = {
        "type": "tree",
        "title": "Estrutura",
        "root": {"code": "90260144", "description": "CABO", "children": []},
    }

    decision = ChatPresentationDecisionService.decide(
        intent="structure_lookup",
        user_message="consulta",
        tree_presentation=tree,
        table_presentation={
            "type": "table",
            "title": "Componentes",
            "columns": [{"key": "code", "label": "Código"}],
            "rows": [{"code": "1"}],
        },
        rows=[{"code": "1"}],
    )

    assert decision["selected"] == "tree"


def test_sale_pricing_profile_path_prefers_text_narrative():
    assert ChatPresentationOperationalDecisionService.should_prefer_pricing_narrative(
        path="/products/90269001/pricing",
        entity="product_pricing",
        intent_token="lookup",
        message="detalhe",
        row_count=4,
        has_text=True,
    )


def test_stock_profile_path_prefers_table_for_few_rows_with_chart():
    assert ChatPresentationOperationalDecisionService.should_prefer_stock_table_over_chart(
        path="/products/90269001/stock",
        entity="product_stock",
        intent_token="stock_lookup",
        row_count=2,
        has_chart=True,
    )


def test_factory_status_text_builder_from_profile():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    path = "/products/90269002/factory-status"

    text = ChatPresentationProfileTextBuilderService.build(
        presenter,
        envelope,
        path=path,
        entity="product_factory_status",
    )

    assert isinstance(text, dict)
    assert text.get("type") == "markdown"
    assert str(text.get("markdown") or "").strip()
