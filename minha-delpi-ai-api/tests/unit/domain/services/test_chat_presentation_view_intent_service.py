"""Intenção de visualização e forma auditável — Playbook 09."""

from __future__ import annotations

from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)
from app.domain.services.chat_presentation_view_intent_service import (
    ChatPresentationViewIntentService,
    VIEW_INTENT_AUDITABLE_LIST,
    VIEW_INTENT_RANKING,
)


def _production_schedule_rows(count: int = 50) -> list[dict]:
    return [
        {
            "production_order": f"OP-{index:04d}",
            "product_code": "70260010",
            "description": "CHICOTE BUHLER 0020/02917",
            "planned_quantity": 0,
            "unit": "UN",
            "priority": 500,
        }
        for index in range(count)
    ]


def test_auditable_list_shape_detected_for_multi_column_operational_rows():
    rows = _production_schedule_rows(3)
    shape = ChatPresentationDataShapeAnalyzer.analyze(rows=rows)

    assert shape["viewIntent"] == VIEW_INTENT_AUDITABLE_LIST
    assert shape["recommended"] == "table"


def test_ranking_shape_detected_for_single_metric_categories():
    rows = [
        {"filial": "01", "saldo": 120},
        {"filial": "02", "saldo": 80},
        {"filial": "03", "saldo": 45},
        {"filial": "04", "saldo": 12},
    ]
    shape = ChatPresentationDataShapeAnalyzer.analyze(rows=rows)

    assert shape["viewIntent"] == VIEW_INTENT_RANKING
    assert shape["recommended"] in {"horizontal_bar", "donut", "bar_chart"}


def test_prefers_table_for_automatic_on_auditable_shape_without_profile():
    rows = _production_schedule_rows(5)

    assert ChatPresentationViewIntentService.prefers_table_for_automatic(
        path="/unknown/route",
        entity=None,
        data_shape=ChatPresentationDataShapeAnalyzer.analyze(rows=rows),
        user_message="quais os produtos programados para produzir hoje",
        has_table=True,
    )


def test_compute_scores_prefers_table_for_auditable_shape_and_listing_message():
    rows = _production_schedule_rows(50)
    shape = ChatPresentationDataShapeAnalyzer.analyze(rows=rows)

    scores = ChatPresentationDecisionService.compute_scores(
        data_shape=shape,
        available_views=["text", "table", "chart"],
        user_message="quais os produtos programados para produzir hoje",
    )

    assert scores["table"] > scores["chart"]


def test_entity_set_profile_contract_matches_playbook_operational():
    from app.domain.services.chat_presentation_profile_service import (
        ChatPresentationProfileService,
    )

    contract = ChatPresentationProfileService.resolve_profile_contract(
        "production_schedule_today",
        path="/production/schedule/today",
    )

    assert contract is not None
    assert contract["matchesExpected"] is True
    assert contract["isDisallowed"] is False


def test_find_entity_set_profile_gaps_is_empty_on_current_matrix():
    from app.domain.services.chat_presentation_coverage_service import (
        ChatPresentationCoverageService,
    )

    gaps = ChatPresentationCoverageService.find_entity_set_profile_gaps()

    assert gaps == []
