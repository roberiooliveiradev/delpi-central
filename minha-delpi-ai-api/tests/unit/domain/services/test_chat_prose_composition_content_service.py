from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_prose_composition_content_service import (
    ChatProseCompositionContentService,
)

configure_domain_infrastructure_ports()


def test_marker_catalog_has_core_kinds():
    kinds = set(ChatProseCompositionContentService.canonical_marker_kinds())

    assert {"table", "tree", "chart", "kpi", "dashboard"} <= kinds


def test_normalize_marker_kind_aliases():
    assert ChatProseCompositionContentService.normalize_marker_kind("tabela") == "table"
    assert ChatProseCompositionContentService.normalize_marker_kind("árvore") == "tree"
    assert ChatProseCompositionContentService.normalize_marker_kind("grafico") == "chart"


def test_policy_nodes_and_explicit_format():
    assert ChatProseCompositionContentService.llm_may_emit_markers("llm_markers_stack") is True
    assert ChatProseCompositionContentService.llm_may_emit_markers("api_only") is False
    assert (
        ChatProseCompositionContentService.policy_for_explicit_format("table") == "api_only"
    )
    assert (
        ChatProseCompositionContentService.policy_for_explicit_format("automatic")
        == "llm_markers_stack"
    )


def test_forbidden_when_explicit_table():
    forbidden = ChatProseCompositionContentService.forbidden_markers_for_explicit("table")

    assert "tree" in forbidden
    assert "chart" in forbidden


def test_max_markers_respects_fast_mode():
    assert ChatProseCompositionContentService.max_markers("llm_markers_stack", response_mode="fast") == 1
    assert ChatProseCompositionContentService.max_markers("llm_markers", response_mode="thinker") >= 4


def test_prompt_rules_format():
    text = ChatProseCompositionContentService.prompt_rule(
        "markerCatalogLine",
        markers="[[table]], [[tree]]",
    )

    assert "[[table]]" in text
    assert "[[tree]]" in text


def test_profile_policy_for_structure_and_stock():
    from app.domain.services.chat_presentation_profile_service import (
        ChatPresentationProfileService,
    )

    assert (
        ChatPresentationProfileService.prose_composition_policy(profile_key="tree_hierarchy")
        == "llm_markers_stack"
    )
    assert (
        ChatPresentationProfileService.prose_composition_policy(profile_key="stock")
        == "llm_markers_stack"
    )
