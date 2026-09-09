"""Unit tests — PresentationChartCompilerService (heatmap + paletteFamily)."""

from __future__ import annotations

from app.domain.entities.presentation_spec import EncodingChannel, PresentationSpec
from app.domain.services.presentation_compilers.presentation_chart_compiler_service import (
    PresentationChartCompilerService,
)
from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)
from app.domain.services.presentation_deterministic_intent_binder_service import (
    PresentationDeterministicIntentBinderService,
)
from app.domain.services.presentation_intent_extractor_service import (
    PresentationIntentExtractorService,
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


def test_heatmap_rebinds_data_from_table_and_sets_palette_family():
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
    }
    PresentationChartCompilerService.apply(
        metadata,
        spec=result.spec,
        labels=profile.resolved_field_labels.get("labels") or {},
        formats={},
    )
    chart = metadata["chartPresentation"]
    assert chart["chartType"] == "heatmap"
    assert len(chart["data"]) == len(rows)
    assert chart["config"]["paletteFamily"] == "sequential-blue"
    assert chart["config"]["colors"] == [
        "var(--mdc-heatmap-low)",
        "var(--mdc-heatmap-high)",
    ]
    assert chart["config"]["bindingProvenance"] == "COMPILED"
    assert {chart["config"]["xAxis"], chart["config"]["yAxis"]} == {
        "product_code",
        "warehouse",
    }


def test_materializes_heatmap_from_table_only_metadata():
    rows = _matrix_rows()
    profile = PresentationDataProfileBuilderService.build(rows)
    intent = PresentationIntentExtractorService.extract(
        "Agora coloque isso em um gráfico de mapa de calor.",
        requested_presentation="table",
    )
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    result = PresentationSpecValidatorService.validate(
        spec, profile=profile, user_explicit=True
    )
    assert result.ok is True

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
    }
    PresentationChartCompilerService.apply(
        metadata,
        spec=result.spec,
        labels={},
        formats={},
    )
    chart = metadata.get("chartPresentation")
    assert isinstance(chart, dict)
    assert chart["type"] == "chart"
    assert chart["chartType"] == "heatmap"
    assert chart["config"]["valueKey"] == "planned_qty"
    assert "unit" not in {
        chart["config"].get("xAxis"),
        chart["config"].get("yAxis"),
    }
