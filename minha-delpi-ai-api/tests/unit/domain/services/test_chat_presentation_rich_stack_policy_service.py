from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)
from app.domain.services.chat_presentation_rich_stack_policy_service import (
    ChatPresentationRichStackPolicyService,
)


def test_structure_exclusivity_defaults_to_text_stack_with_tree_and_kpi():
    metadata = {
        "path": "/products/90261805/structure/exclusivity",
        "apiDelpiResponseMeta": {"entity": "product_structure_exclusivity"},
        "textPresentation": {"type": "markdown", "markdown": "### Estrutura\n\nResumo."},
        "treePresentation": {"type": "tree", "title": "BOM", "root": {"id": "90261805", "children": []}},
        "kpiPresentation": {"type": "kpi", "title": "Resumo", "cards": []},
        "tablePresentations": [
            {"type": "table", "title": "Resumo da estrutura", "rows": [{"campo": "MPs", "valor": "2"}]},
        ],
    }

    assert ChatPresentationRichStackPolicyService.should_default_to_text_stack(
        path=metadata["path"],
        metadata=metadata,
        entity="product_structure_exclusivity",
    )

    views = ChatPresentationRichStackPolicyService.resolve_available_views(
        metadata,
        path=metadata["path"],
        entity="product_structure_exclusivity",
    )

    assert views[0] == "text"
    assert "tree" in views
    assert "kpi" in views


def test_decision_service_uses_rich_stack_for_factory_status():
    metadata = {
        "path": "/products/90269002/factory-status",
        "apiDelpiResponseMeta": {"entity": "product_factory_status"},
        "textPresentation": {"type": "markdown", "markdown": "### Status fabril\n\n**Destaques**\n\n- OK."},
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "90269002", "children": []}},
        "kpiPresentation": {"type": "kpi", "title": "KPI", "cards": []},
        "tablePresentations": [
            {"type": "table", "title": "Panorama fabril", "rows": [{"campo": "A", "valor": "1"}]},
        ],
        "availableFormats": ["text", "table", "tree", "kpi", "dashboard"],
    }

    ChatPresentationDecisionService.enrich_metadata(metadata)

    decision = metadata["presentationDecision"]

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "stack"
    assert "tree" in decision["availableViews"]


def test_tail_visual_order_follows_profile_view_order():
    metadata = {
        "path": "/products/90261805/structure/exclusivity",
        "apiDelpiResponseMeta": {"entity": "product_structure_exclusivity"},
        "textPresentation": {"type": "markdown", "markdown": "Resumo"},
        "kpiPresentation": {"type": "kpi", "title": "KPI", "cards": []},
        "treePresentation": {"type": "tree", "title": "BOM", "root": {"id": "root", "children": []}},
        "chartPresentation": {"type": "chart", "title": "Chart", "data": []},
    }

    order = ChatPresentationRichStackPolicyService.resolve_tail_visual_order(
        metadata,
        path=metadata["path"],
        entity="product_structure_exclusivity",
    )

    assert order.index("tree") < order.index("chart")
    assert order.index("chart") < order.index("kpi")
