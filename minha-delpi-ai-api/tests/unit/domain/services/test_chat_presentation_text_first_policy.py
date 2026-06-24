from app.domain.services.chat_presentation_text_first_policy_service import (
    ChatPresentationTextFirstPolicyService,
)


def test_stock_simple_question_keeps_table_primary_without_visual_bundle():
    assert not ChatPresentationTextFirstPolicyService.should_default_to_text_only(
        path="/products/10080001/stock",
        entity="product_stock",
        user_message="estoque do produto 10080001",
    )
    assert not ChatPresentationTextFirstPolicyService.should_build_visual_bundle(
        path="/products/10080001/stock",
        entity="product_stock",
        user_message="estoque do produto 10080001",
    )


def test_explicit_chart_request_builds_visual_bundle():
    assert ChatPresentationTextFirstPolicyService.should_build_visual_bundle(
        path="/products/10080001/stock",
        entity="product_stock",
        explicit_format="chart",
    )


def test_integrated_stack_request_builds_visual_bundle():
    assert ChatPresentationTextFirstPolicyService.should_build_visual_bundle(
        path="/products/10080001/stock",
        entity="product_stock",
        user_message="estoque completo do produto 10080001",
    )
    assert ChatPresentationTextFirstPolicyService.looks_like_integrated_stack_request(
        "mostre a visão integrada do estoque",
    )


def test_apply_text_primary_keeps_tree_for_structure_text_outline():
    from app.domain.services.chat_presentation_primary_view_service import (
        ChatPresentationPrimaryViewService,
    )

    metadata = {
        "path": "/products/90260149/structure",
        "textPresentation": {"type": "markdown", "markdown": "### Estrutura\n\nResumo."},
        "presentation": {
            "type": "tree",
            "title": "Estrutura",
            "root": {"id": "90260149", "label": "90260149", "children": []},
        },
        "chartPresentation": {"type": "chart", "data": []},
        "availableFormats": ["text", "tree", "chart"],
    }

    applied = ChatPresentationPrimaryViewService.apply_session_preference(metadata, "text")

    assert applied is True
    assert metadata.get("presentation") is None
    assert metadata.get("treePresentation", {}).get("type") == "tree"


def test_apply_text_primary_skips_stock_when_table_is_primary():
    metadata = {
        "textPresentation": {"type": "markdown", "markdown": "### Estoque\n\n- Filial 01"},
        "presentation": {"type": "table", "rows": [{"branch": "01"}]},
        "chartPresentation": {"type": "chart", "data": []},
        "treePresentation": {"type": "tree", "nodes": []},
        "availableFormats": ["text", "table", "chart", "tree"],
    }

    applied = ChatPresentationTextFirstPolicyService.apply_text_primary_metadata(
        metadata,
        path="/products/10080001/stock",
        entity="product_stock",
        user_message="estoque do produto 10080001",
    )

    assert applied is False
    assert metadata.get("presentation", {}).get("type") == "table"
    assert metadata.get("chartPresentation", {}).get("type") == "chart"
