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


def test_user_preference_tree_requires_tree_presentation():
    tree = {
        "type": "tree",
        "title": "Estrutura",
        "root": {"id": "90260144", "label": "90260144", "children": []},
    }

    decision = ChatPresentationDecisionService.decide(
        user_preference="tree",
        user_message="estrutura",
        tree_presentation=tree,
        available_formats=["tree", "table", "text"],
        table_presentation={
            "type": "table",
            "title": "Componentes",
            "columns": [{"key": "code", "label": "Código"}],
            "rows": [{"code": "1"}],
        },
        rows=[{"code": "1"}],
    )

    assert decision["selected"] == "tree"


def test_user_preference_tree_accepts_primary_tree_presentation():
    tree = {
        "type": "tree",
        "title": "Estrutura",
        "root": {"id": "90260144", "label": "90260144", "children": []},
    }

    decision = ChatPresentationDecisionService.decide(
        user_preference="tree",
        user_message="me fale do produto 90260144",
        primary_presentation=tree,
        available_formats=["tree", "table", "text"],
        table_presentation={
            "type": "table",
            "title": "Produto",
            "columns": [{"key": "campo", "label": "Campo"}],
            "rows": [{"campo": "Código", "valor": "90260144"}],
        },
        rows=[{"campo": "Código", "valor": "90260144"}],
    )

    assert decision["selected"] == "tree"


def test_enrich_metadata_analyser_puts_tree_before_table_in_visual_order():
    tree = {
        "type": "tree",
        "title": "Estrutura",
        "root": {"id": "90260144", "label": "90260144", "children": []},
    }
    metadata = {
        "path": "/products/90260144/analyser",
        "presentation": tree,
        "tablePresentation": {
            "type": "table",
            "title": "Produto",
            "columns": [{"key": "campo", "label": "Campo"}],
            "rows": [{"campo": "Código", "valor": "90260144"}],
        },
        "textPresentation": {"type": "markdown", "markdown": "Resumo"},
        "availableFormats": ["text", "tree", "table"],
        "preferredFormat": "tree",
    }

    ChatPresentationDecisionService.enrich_metadata(metadata)

    order = metadata["presentationDecision"]["visualOrder"]

    assert order.index("table") < order.index("tree")
    assert metadata["presentationDecision"]["selected"] == "text"
    assert "stack" in metadata["presentationDecision"]["reason"].lower()


def test_enrich_metadata_analyser_honors_explicit_tree_preference():
    tree = {
        "type": "tree",
        "title": "Estrutura",
        "root": {"id": "90260144", "label": "90260144", "children": []},
    }
    metadata = {
        "path": "/products/90260144/analyser",
        "presentation": tree,
        "textPresentation": {"type": "markdown", "markdown": "Resumo"},
        "availableFormats": ["text", "tree", "table"],
        "preferredFormat": "tree",
    }

    ChatPresentationDecisionService.enrich_metadata(
        metadata,
        user_preference="tree",
        user_message="mostre em árvore",
    )

    assert metadata["presentationDecision"]["selected"] == "tree"
