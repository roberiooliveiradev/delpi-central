"""E4.S1 — matriz compose e Automático sem chart quando chartPolicy=skip."""

from __future__ import annotations

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_schema_driven_presentation_service import (
    ChatSchemaDrivenPresentationService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.chat_presentation_compose_matrix import (
    COMPOSE_FORMAT_PRECEDENCE,
    COMPOSE_MATRIX_CASES,
)


def test_compose_format_precedence_is_documented():
    assert COMPOSE_FORMAT_PRECEDENCE == (
        "explicitSessionFormat",
        "messageHints",
        "automatic",
    )


def test_stock_profile_chart_policy_skip_and_table_when_available():
    profile = ChatPresentationProfileService.resolve_profile(
        "/products/10090016/stock",
        "product_stock",
    )
    assert str(profile.get("chartPolicy") or "").lower() == "skip"
    assert str(profile.get("defaultViewPolicy") or "") == "table_when_available"
    decision = profile.get("presentationDecision") or {}
    assert decision.get("narrativeFirstMaxRows") == 0


def test_compose_matrix_auto_stock_never_selects_chart_without_slot():
    """Automático + stock: bundle sem chart; decisão não deve preferir chart."""
    from app.domain.services.chat_presentation_decision_service import (
        ChatPresentationDecisionService,
    )

    presenter = ExternalActionResultPresenter()
    rows = [
        {
            "branch": "01",
            "warehouse": "01",
            "available_quantity": 0,
            "current_quantity": 0,
            "committed_quantity": 0,
        },
        {
            "branch": "01",
            "warehouse": "99",
            "available_quantity": 1,
            "current_quantity": 1,
            "committed_quantity": 0,
        },
        {
            "branch": "02",
            "warehouse": "01",
            "available_quantity": 2,
            "current_quantity": 2,
            "committed_quantity": 0,
        },
        {
            "branch": "02",
            "warehouse": "02",
            "available_quantity": 0,
            "current_quantity": 0,
            "committed_quantity": 0,
        },
    ]
    bundle = ChatSchemaDrivenPresentationService.build_bundle(
        presenter,
        {"items": rows},
        path="/products/10090016/stock",
        entity="product_stock",
    )
    assert bundle.chart is None
    assert bundle.table is not None

    metadata = {
        "path": "/products/10090016/stock",
        "tablePresentation": bundle.table,
        "textPresentation": bundle.text,
        "kpiPresentation": bundle.kpi,
        "chartPresentation": bundle.chart,
        "treePresentation": bundle.tree,
        "presentation": bundle.table or bundle.text,
        "availableFormats": ["table", "text"] if bundle.table else ["text"],
    }
    decision = ChatPresentationDecisionService.decide(
        metadata=metadata,
        path="/products/10090016/stock",
        user_message="estoque do produto 10090016",
        primary_presentation=bundle.table or bundle.text,
        table_presentation=bundle.table,
        chart_presentation=bundle.chart,
        tree_presentation=bundle.tree,
        text_presentation=bundle.text,
        available_formats=["table", "text"] if bundle.table else ["text"],
        rows=rows,
    )
    selected = str((decision or {}).get("selected") or "").lower()
    assert selected != "chart"
    assert selected in {"table", "text", "kpi"}
    assert selected == "table"


def test_compose_matrix_cases_cover_stock_toolbar_variants():
    ids = {case["id"] for case in COMPOSE_MATRIX_CASES}
    assert "auto_stock_table_lead" in ids
    assert "toolbar_table_stock" in ids
    assert "toolbar_chart_stock_skip_policy" in ids
    for case in COMPOSE_MATRIX_CASES:
        if case.get("chart_policy") == "skip":
            assert case.get("expect_chart_slot") is False
