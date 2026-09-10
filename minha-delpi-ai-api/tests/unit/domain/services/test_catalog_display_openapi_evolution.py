"""Unit tests — ActionDisplayLabelResolver + ResultPresentationTitleResolver + recommendations."""

from __future__ import annotations

import os

from app.domain.services.action_display_label_resolver import (
    SOURCE_OPENAPI_SUMMARY,
    ActionDisplayLabelResolver,
)
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.recommendation_action_validator import (
    RecommendationActionValidator,
)
from app.domain.services.result_presentation_title_resolver import (
    SOURCE_ACTION_DISPLAY_LABEL,
    SOURCE_PRESENTATION_TITLE,
    SOURCE_SLOT_TITLE,
    ResultPresentationTitleResolver,
)


def test_action_display_prefers_portuguese_summary(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/products/{code}/stock",
        method="GET",
        summary="Consultar estoque do produto por filial",
    )
    assert result.label == "Consultar estoque do produto por filial"
    assert result.source == SOURCE_OPENAPI_SUMMARY


def test_action_display_english_summary_uses_locale_not_path_label(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/commercial/closing-rate",
        method="GET",
        summary="Get Sales Conversion Rate",
        delpi_metadata={
            "locale": {"pt-BR": {"summary": "Taxa de conversão de vendas"}},
        },
    )
    assert result.label == "Taxa de conversão de vendas"
    assert result.source == "OPENAPI_LOCALIZED"


def test_action_display_locale_beats_english_summary(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/products/{code}/stock",
        method="GET",
        summary="Get product stock",
        delpi_metadata={
            "locale": {"pt-BR": {"summary": "Consultar estoque do produto por filial"}},
        },
    )
    assert result.source == "OPENAPI_LOCALIZED"
    assert "Consultar estoque" in result.label


def test_action_display_unknown_api_without_path_label(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/acme/widgets/{id}/inventory",
        method="GET",
        summary="Widget inventory by warehouse",
        action_id="acme.widgets.inventory",
        provider_key="acme-erp",
    )
    assert result.label
    assert result.source != "LEGACY_PATH_LABEL"


def test_action_display_metamorphic_rename_same_summary(monkeypatch):
    summary = "Consultar disponibilidade de item"
    a = ActionDisplayLabelResolver.resolve(
        path="/v1/widgets/{id}/availability",
        method="GET",
        summary=summary,
        action_id="widgets.availability.v1",
        provider_key="acme",
    )
    b = ActionDisplayLabelResolver.resolve(
        path="/catalog/sku/{sku}/availability",
        method="GET",
        summary=summary,
        action_id="catalog.sku.availability",
        provider_key="acme",
    )
    assert a.label == b.label == summary
    assert a.source == b.source == SOURCE_OPENAPI_SUMMARY


def test_presentation_title_prefers_slot_then_metadata(monkeypatch):
    slot = ResultPresentationTitleResolver.resolve(
        path="/products/X/stock",
        slot_title="Estoque — X",
        legacy_title="Estoque",
    )
    assert slot.title == "Estoque — X"
    assert slot.source == SOURCE_SLOT_TITLE

    meta = ResultPresentationTitleResolver.resolve(
        path="/products/X/stock",
        metadata={"presentation": {"title": "Posição de estoque"}},
        legacy_title="Estoque",
    )
    assert meta.title == "Posição de estoque"
    assert meta.source == SOURCE_PRESENTATION_TITLE


def test_presentation_title_falls_back_to_action_label(monkeypatch):
    resolved = ResultPresentationTitleResolver.resolve(
        path="/acme/widgets",
        summary="Lista de widgets",
        legacy_title=None,
        fallback="Resultado",
    )
    assert resolved.title == "Lista de widgets"
    assert resolved.source == SOURCE_ACTION_DISPLAY_LABEL


def test_recommendation_validator_rejects_unauthorized_action():
    items = RecommendationActionValidator.filter_items(
        [
            {"label": "Ver estoque", "query": "estoque", "actionId": "allowed.stock"},
            {"label": "Hack", "query": "hack", "actionId": "forbidden.write"},
            {"label": "Só texto", "query": "texto"},
        ],
        ["allowed.stock"],
    )
    action_ids = {item.get("actionId") for item in items if item.get("actionId")}
    assert action_ids == {"allowed.stock"}
    assert any(item.get("label") == "Só texto" for item in items)


def test_normalize_uses_structured_recommendations_with_allowlist():
    commentary = ChatHumanizedDataResponseService.normalize(
        {
            "highlights": ["ok"],
            "structuredRecommendations": [
                {"label": "Estoque", "query": "estoque", "actionId": "a1"},
                {"label": "Proibido", "query": "x", "actionId": "a2"},
            ],
        },
        profile_key="generic_list",
        allowed_action_ids=["a1"],
    )
    assert commentary is not None
    recs = commentary.get("recommendations") or []
    assert len(recs) == 1
    assert recs[0].get("actionId") == "a1"


def test_commentary_highlight_uses_resolved_field_labels():
    from app.domain.services.chat_data_insight_service import ChatDataInsightService

    lines = ChatDataInsightService._highlights_from_operational_summary(
        {"summary": {"oee_pct": 87.5, "late_ops": 3}},
        metadata={
            "resolvedFieldLabels": {
                "labels": {
                    "oee_pct": "OEE %",
                    "late_ops": "OPs em atraso",
                },
                "sourceByKey": {
                    "oee_pct": "OPENAPI",
                    "late_ops": "OPENAPI",
                },
            }
        },
    )
    joined = " ".join(lines)
    assert "OEE %" in joined
    assert "OPs em atraso" in joined
