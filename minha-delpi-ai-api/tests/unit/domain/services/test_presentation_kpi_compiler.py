"""Unit tests — PresentationKpiCompilerService."""

from __future__ import annotations

from app.domain.entities.presentation_spec import PresentationKpiSpec, PresentationSpec
from app.domain.services.presentation_compilers.presentation_kpi_compiler_service import (
    PresentationKpiCompilerService,
)
from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)


def _rows():
    return [
        {"product_code": "P1", "planned_qty": 10, "balance": 100.5},
        {"product_code": "P2", "planned_qty": 20, "balance": 50.0},
        {"product_code": "P3", "planned_qty": 5, "balance": 25.25},
    ]


def test_kpi_compiler_aggregates_measures_with_audit_trail():
    rows = _rows()
    profile = PresentationDataProfileBuilderService.build(rows)
    spec = PresentationSpec(
        view="kpi",
        kpi=PresentationKpiSpec(
            measure_fields=("planned_qty", "balance"),
            card_order=("balance", "planned_qty"),
            tones=("success", "brand"),
        ),
        labels={"planned_qty": "Qtd. planejada", "balance": "Saldo"},
        formats={"balance": "currency"},
    )
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": "planned_qty"}, {"key": "balance"}],
            "rows": rows,
        }
    }
    PresentationKpiCompilerService.apply(
        metadata,
        spec=spec,
        profile=profile,
        labels=spec.labels,
        formats=spec.formats,
    )

    cards = metadata["kpiPresentation"]["cards"]
    assert len(cards) == 2
    assert cards[0]["key"] == "balance"
    assert cards[0]["value"] == 175.75
    assert cards[0]["label"] == "Saldo"
    assert cards[0]["color"] == "var(--mdc-chart-series-3)"
    assert cards[0]["tone"] == "success"
    assert cards[1]["key"] == "planned_qty"
    assert cards[1]["value"] == 35

    audit = metadata["presentationIntelligence"]["kpiAudit"]
    assert audit[0]["field"] == "balance"
    assert audit[0]["aggregation"] == "sum"
    assert audit[0]["nonNullCount"] == 3


def test_kpi_compiler_does_not_invent_values_without_rows():
    profile = PresentationDataProfileBuilderService.build([])
    spec = PresentationSpec(
        view="kpi",
        kpi=PresentationKpiSpec(measure_fields=("planned_qty",)),
    )
    metadata: dict = {}
    PresentationKpiCompilerService.apply(
        metadata,
        spec=spec,
        profile=profile,
        labels={},
        formats={},
    )
    assert metadata.get("kpiPresentation") is None


def test_kpi_compiler_caps_at_eight_cards():
    measures = tuple(f"measure_{index}" for index in range(10))
    rows = [{field: float(index + 1) for field in measures} for index in range(3)]
    profile = PresentationDataProfileBuilderService.build(rows)
    spec = PresentationSpec(
        view="kpi",
        kpi=PresentationKpiSpec(measure_fields=measures),
    )
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": key} for key in measures],
            "rows": rows,
        }
    }
    PresentationKpiCompilerService.apply(
        metadata,
        spec=spec,
        profile=profile,
        labels={},
        formats={},
    )
    assert len(metadata["kpiPresentation"]["cards"]) == 8
