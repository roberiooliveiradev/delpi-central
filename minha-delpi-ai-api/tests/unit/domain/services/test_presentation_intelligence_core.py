"""Unit tests — PresentationSpec validator/compiler + heatmap axes."""

from __future__ import annotations

from app.domain.entities.presentation_spec import EncodingChannel, PresentationSpec
from app.domain.services.chat_chart_type_selection_service import (
    ChatChartTypeSelectionService,
)
from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)
from app.domain.services.presentation_intent_extractor_service import (
    PresentationIntentExtractorService,
)
from app.domain.services.presentation_deterministic_intent_binder_service import (
    PresentationDeterministicIntentBinderService,
)
from app.domain.services.presentation_spec_compiler_service import (
    PresentationSpecCompilerService,
)
from app.domain.services.presentation_spec_validator_service import (
    PresentationSpecValidatorService,
)


def _matrix_rows():
    rows = []
    for product in ("P1", "P2"):
        for wh in ("W1", "W2", "W3"):
                    rows.append(
                        {
                            "product_code": product,
                            "warehouse": wh,
                            "unit": "UN",
                            "planned_qty": 10 + (10 if product == "P2" else 0) + len(wh) * 3,
                        }
                    )
    return rows


def test_heatmap_axes_skip_constant_unit():
    rows = _matrix_rows()
    x, y = ChatChartTypeSelectionService._pick_heatmap_axes(
        ["product_code", "warehouse", "unit"],
        rows,
    )
    assert {x, y} == {"product_code", "warehouse"}
    assert "unit" not in {x, y}


def test_validator_rejects_heatmap_with_constant_y():
    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(rows)
    spec = PresentationSpec(
        view="chart",
        mark="heatmap",
        encoding={
            "x": EncodingChannel(field="warehouse"),
            "y": EncodingChannel(field="unit"),
            "color": EncodingChannel(field="planned_qty"),
        },
    )
    result = PresentationSpecValidatorService.validate(spec, profile=profile, user_explicit=True)
    assert result.ok is False
    assert result.unmet_intent == "heatmap_not_materializable"


def test_validator_accepts_valid_heatmap_and_compiler_sets_labels():
    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle={
            "labels": {
                "product_code": "Produto",
                "warehouse": "Depósito",
                "planned_qty": "Qtd. planejada",
            },
            "formats": {},
            "sourceByKey": {},
        },
    )
    spec = PresentationSpec(
        view="chart",
        mark="heatmap",
        encoding={
            "x": EncodingChannel(field="warehouse", type="nominal"),
            "y": EncodingChannel(field="product_code", type="nominal"),
            "color": EncodingChannel(
                field="planned_qty",
                type="quantitative",
                scale="sequential-blue",
            ),
        },
        palette_family="sequential-blue",
        provenance="DETERMINISTIC",
    )
    result = PresentationSpecValidatorService.validate(spec, profile=profile)
    assert result.ok is True
    assert result.spec is not None

    metadata = {
        "chartPresentation": {
            "type": "chart",
            "chartType": "bar",
            "title": "t",
            "data": rows,
            "config": {},
        }
    }
    PresentationSpecCompilerService.compile_into_metadata(
        metadata,
        spec=result.spec,
        profile=profile,
    )
    chart = metadata["chartPresentation"]
    assert chart["chartType"] == "heatmap"
    assert chart["config"]["xAxis"] == "warehouse"
    assert chart["config"]["yAxis"] == "product_code"
    assert chart["config"]["valueKey"] == "planned_qty"
    assert chart["config"]["fieldLabels"]["planned_qty"] == "Qtd. planejada"
    assert chart["config"]["bindingProvenance"] == "COMPILED"
    assert chart["config"]["paletteFamily"] == "sequential-blue"


def test_validator_rejects_label_as_field_identity():
    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(rows)
    spec = PresentationSpec(
        view="chart",
        mark="bar",
        encoding={"x": EncodingChannel(field="Produto")},
        labels={"product_code": "Produto"},
    )
    result = PresentationSpecValidatorService.validate(spec, profile=profile)
    assert result.ok is False or "Produto" not in {
        channel.field for channel in (result.spec.encoding.values() if result.spec else [])
    }


def test_intent_binder_heatmap_from_portuguese_message():
    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle={
            "labels": {
                "product_code": "Produto",
                "warehouse": "Depósito",
                "planned_qty": "Qtd. planejada",
            },
            "formats": {},
            "sourceByKey": {},
        },
    )
    intent = PresentationIntentExtractorService.extract(
        "mapa de calor produto × depósito com qtd planejada em tons de azul"
    )
    assert intent.mark == "heatmap"
    assert intent.palette_family == "sequential-blue"
    spec, confidence = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    assert confidence >= 0.55
    assert spec.mark == "heatmap"
    assert spec.encoding["color"].field == "planned_qty"


def test_compiler_rebinds_heatmap_data_from_table_when_chart_is_aggregated():
    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle={
            "labels": {
                "product_code": "Produto",
                "warehouse": "Depósito",
                "planned_qty": "Qtd. planejada",
            },
            "formats": {},
            "sourceByKey": {},
        },
    )
    intent = PresentationIntentExtractorService.extract(
        "Agora coloque isso em um gráfico de mapa de calor.",
        requested_presentation="table",
    )
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    result = PresentationSpecValidatorService.validate(spec, profile=profile, user_explicit=True)
    assert result.ok
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [
                {"key": "product_code"},
                {"key": "warehouse"},
                {"key": "planned_qty"},
            ],
            "rows": rows,
        },
        "presentation": {
            "type": "chart",
            "chartType": "bar",
            "data": [{"operation_start_date": "20260909", "planned_qty": 7620}],
            "config": {"xAxis": "operation_start_date", "yAxis": "planned_qty"},
        },
        "presentationDecision": {"selected": "table", "layoutMode": "single"},
    }
    PresentationSpecCompilerService.compile_into_metadata(
        metadata, spec=result.spec, profile=profile
    )
    chart = metadata["chartPresentation"]
    assert chart["chartType"] == "heatmap"
    assert len(chart["data"]) == len(rows)
    assert {chart["config"]["xAxis"], chart["config"]["yAxis"]} == {
        "product_code",
        "warehouse",
    }


def test_compiler_materializes_heatmap_from_table_only_metadata():
    """Follow-up «mapa de calor» sobre lista: table slot exists, chart must be created."""
    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle={
            "labels": {
                "product_code": "Produto",
                "warehouse": "Depósito",
                "planned_qty": "Qtd. planejada",
            },
            "formats": {},
            "sourceByKey": {},
        },
    )
    intent = PresentationIntentExtractorService.extract(
        "Agora coloque isso em um gráfico de mapa de calor.",
        requested_presentation="table",
    )
    assert intent.mark == "heatmap"
    assert intent.view == "chart"
    spec, confidence = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    assert confidence >= 0.55
    result = PresentationSpecValidatorService.validate(
        spec, profile=profile, user_explicit=True
    )
    assert result.ok is True

    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [
                {"key": "product_code", "label": "product_code"},
                {"key": "warehouse", "label": "warehouse"},
                {"key": "planned_qty", "label": "planned_qty"},
            ],
            "rows": rows,
        },
        "presentationDecision": {"selected": "table", "layoutMode": "single"},
    }
    PresentationSpecCompilerService.compile_into_metadata(
        metadata,
        spec=result.spec,
        profile=profile,
    )
    chart = metadata.get("chartPresentation")
    assert isinstance(chart, dict)
    assert chart["type"] == "chart"
    assert chart["chartType"] == "heatmap"
    assert chart["config"]["valueKey"] == "planned_qty"
    assert chart["config"]["bindingProvenance"] == "COMPILED"
    assert metadata["presentationDecision"]["selected"] == "heatmap"
    assert "unit" not in {
        chart["config"].get("xAxis"),
        chart["config"].get("yAxis"),
    }


def test_compiler_materializes_bar_sibling_from_table_only_metadata():
    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(rows)
    intent = PresentationIntentExtractorService.extract(
        "Mostre isso em gráfico de barras.",
        requested_presentation="table",
    )
    assert intent.view == "chart"
    spec, _confidence = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    result = PresentationSpecValidatorService.validate(spec, profile=profile)
    assert result.ok is True
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": "product_code"}, {"key": "planned_qty"}],
            "rows": rows,
        }
    }
    PresentationSpecCompilerService.compile_into_metadata(
        metadata, spec=result.spec, profile=profile
    )
    chart = metadata.get("chartPresentation")
    assert isinstance(chart, dict)
    assert chart["type"] == "chart"


def test_compiler_table_spec_does_not_invent_chart_slot():
    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(rows)
    intent = PresentationIntentExtractorService.extract(
        "Traga a lista de produtos.",
        requested_presentation="table",
    )
    assert intent.view == "table"
    assert intent.mark is None
    spec, _confidence = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    assert spec.view == "table"
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": "product_code"}, {"key": "planned_qty"}],
            "rows": rows,
        }
    }
    PresentationSpecCompilerService.compile_into_metadata(
        metadata, spec=spec, profile=profile
    )
    assert metadata.get("chartPresentation") is None

    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(rows)
    raw = {
        "version": 1,
        "view": "chart",
        "mark": "bar",
        "encoding": {"x": {"field": "warehouse"}, "y": {"field": "planned_qty"}},
        "paletteFamily": "url(javascript:alert(1))",
    }
    result = PresentationSpecValidatorService.validate(raw, profile=profile)
    assert result.ok is False
    assert any(error.startswith("forbidden_style:") for error in result.errors)
    assert result.unmet_intent == "forbidden_presentation_style"