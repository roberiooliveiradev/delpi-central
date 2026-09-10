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


def test_field_label_parity_table_chart_kpi_insight():
    """R4/R5 — same key resolves equivalently for table/chart/KPI/insight via FLB."""
    from app.domain.entities.field_label_bundle import FieldLabelBundle
    from app.domain.entities.presentation_spec import (
        EncodingChannel,
        PresentationKpiSpec,
        PresentationSpec,
        PresentationTableSpec,
    )
    from app.domain.services.chat_data_insight_service import ChatDataInsightService
    from app.domain.services.presentation_compilers.presentation_chart_compiler_service import (
        PresentationChartCompilerService,
    )
    from app.domain.services.presentation_compilers.presentation_kpi_compiler_service import (
        PresentationKpiCompilerService,
    )
    from app.domain.services.presentation_compilers.presentation_table_compiler_service import (
        PresentationTableCompilerService,
    )
    from app.domain.services.presentation_data_profile_builder_service import (
        PresentationDataProfileBuilderService,
    )

    key = "oee_pct"
    expected = "OEE %"
    sibling_key = "late_ops"
    sibling_label = "OPs em atraso"
    labels = {key: expected, sibling_key: sibling_label}
    formats = {key: "percent", sibling_key: "quantity"}
    metadata_labels = {
        "resolvedFieldLabels": {
            "labels": labels,
            "formats": formats,
            "sourceByKey": {
                key: "OPENAPI_TITLE",
                sibling_key: "OPENAPI_TITLE",
            },
        }
    }

    bundle = FieldLabelBundle.from_metadata(metadata_labels)
    assert bundle.label_for(key) == expected
    assert bundle.label_for(sibling_key) == sibling_label

    rows = [
        {key: 87.5, sibling_key: 3, "product_code": "P1"},
        {key: 90.0, sibling_key: 1, "product_code": "P2"},
    ]
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle=metadata_labels["resolvedFieldLabels"],
    )
    shared_labels = dict(profile.resolved_field_labels.get("labels") or {})
    shared_formats = dict(profile.resolved_field_labels.get("formats") or {})
    assert shared_labels[key] == expected

    table_spec = PresentationSpec(
        view="table",
        fields=(key, sibling_key),
        labels=shared_labels,
        formats=shared_formats,
        table=PresentationTableSpec(title="Indicadores"),
    )
    table_meta = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": key}, {"key": sibling_key}],
            "rows": rows,
        }
    }
    PresentationTableCompilerService.apply(
        table_meta,
        spec=table_spec,
        labels=shared_labels,
        formats=shared_formats,
    )
    table_cols = {
        col["key"]: col["label"] for col in table_meta["tablePresentation"]["columns"]
    }
    assert table_cols[key] == expected
    assert table_cols[sibling_key] == sibling_label

    chart_spec = PresentationSpec(
        view="chart",
        mark="bar",
        encoding={
            "x": EncodingChannel(field="product_code", type="nominal"),
            "y": EncodingChannel(field=key, type="quantitative"),
        },
        labels=shared_labels,
        formats=shared_formats,
    )
    chart_meta = {
        "chartPresentation": {
            "type": "chart",
            "chartType": "bar",
            "data": rows,
            "config": {"xAxis": "product_code", "yAxis": key},
        }
    }
    PresentationChartCompilerService.apply(
        chart_meta,
        spec=chart_spec,
        labels=shared_labels,
        formats=shared_formats,
    )
    chart_field_labels = chart_meta["chartPresentation"]["config"]["fieldLabels"]
    assert chart_field_labels[key] == expected

    kpi_spec = PresentationSpec(
        view="kpi",
        kpi=PresentationKpiSpec(measure_fields=(key, sibling_key)),
        labels=shared_labels,
        formats=shared_formats,
    )
    kpi_meta = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": key}, {"key": sibling_key}],
            "rows": rows,
        }
    }
    PresentationKpiCompilerService.apply(
        kpi_meta,
        spec=kpi_spec,
        profile=profile,
        labels=shared_labels,
        formats=shared_formats,
    )
    kpi_labels = {
        card["key"]: card["label"] for card in kpi_meta["kpiPresentation"]["cards"]
    }
    assert kpi_labels[key] == expected
    assert kpi_labels[sibling_key] == sibling_label

    insight_lines = ChatDataInsightService._highlights_from_operational_summary(
        {"summary": {key: 87.5, sibling_key: 3}},
        metadata=metadata_labels,
    )
    joined = " ".join(insight_lines)
    assert expected in joined
    assert sibling_label in joined

    # Negative: unknown key does not invent a parallel catalog label
    assert bundle.label_for("unknown_metric_xyz") == ""
