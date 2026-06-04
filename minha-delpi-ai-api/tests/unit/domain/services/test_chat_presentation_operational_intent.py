from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)


def test_structure_intent_prefers_tree_when_available():
    tree = {
        "type": "tree",
        "title": "Estrutura",
        "root": {"code": "90260144", "description": "CABO", "children": []},
    }

    decision = ChatPresentationDecisionService.decide(
        intent="structure_lookup",
        user_message="estrutura",
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


def test_price_intent_prefers_text_when_text_presentation_exists():
    decision = ChatPresentationDecisionService.decide(
        intent="price_lookup",
        user_message="preço",
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


def test_user_preference_tree_overrides_table_default():
    decision = ChatPresentationDecisionService.decide(
        user_preference="tree",
        user_message="estoque",
        table_presentation={
            "type": "table",
            "title": "Estoque",
            "columns": [{"key": "branch", "label": "Filial"}],
            "rows": [{"branch": "01", "available_quantity": 1}],
        },
        rows=[{"branch": "01", "available_quantity": 1}],
    )

    assert decision["selected"] == "tree"
