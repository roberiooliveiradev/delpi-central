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


def test_adversarial_palette_rejected():
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
    assert result.ok is True
    assert result.spec is not None
    assert result.spec.palette_family is None
