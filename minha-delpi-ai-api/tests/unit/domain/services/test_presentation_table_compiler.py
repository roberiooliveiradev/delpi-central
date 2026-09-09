"""Unit tests — PresentationTableCompilerService."""

from __future__ import annotations

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import (
    PresentationSpec,
    PresentationTableSpec,
)
from app.domain.services.presentation_compilers.presentation_table_compiler_service import (
    PresentationTableCompilerService,
)
from app.domain.services.presentation_spec_compiler_service import (
    PresentationSpecCompilerService,
)


def _rows():
    return [
        {"product_code": "P2", "warehouse": "W2", "planned_qty": 30, "unit": "UN"},
        {"product_code": "P1", "warehouse": "W1", "planned_qty": 10, "unit": "UN"},
        {"product_code": "P1", "warehouse": "W3", "planned_qty": 25, "unit": "UN"},
    ]


def test_table_compiler_orders_three_columns_sorts_and_hides_visual_only():
    spec = PresentationSpec(
        view="table",
        fields=("product_code", "warehouse", "planned_qty"),
        sort_field="planned_qty",
        sort_direction="desc",
        labels={
            "product_code": "Produto",
            "warehouse": "Depósito",
            "planned_qty": "Qtd. planejada",
        },
        formats={"planned_qty": "integer"},
        table=PresentationTableSpec(
            density="compact",
            hidden_fields=("unit",),
            role="operational",
            title="Planejamento",
        ),
    )
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [
                {"key": "planned_qty"},
                {"key": "product_code"},
                {"key": "warehouse"},
                {"key": "unit"},
            ],
            "rows": _rows(),
        }
    }
    PresentationTableCompilerService.apply(
        metadata,
        spec=spec,
        labels=spec.labels,
        formats=spec.formats,
    )

    table = metadata["tablePresentation"]
    column_keys = [col["key"] for col in table["columns"]]
    assert column_keys == ["product_code", "warehouse", "planned_qty"]
    assert "unit" not in column_keys
    assert [col["key"] for col in table["exportColumns"]] == column_keys
    assert table["columns"][2]["dataType"] == "number"
    assert table["config"]["density"] == "compact"
    assert table["config"]["role"] == "operational"
    assert table["title"] == "Planejamento"
    assert table["config"]["exportSourceUnchanged"] is True
    assert len(table["rows"]) == 3
    assert table["rows"][0]["planned_qty"] == 30
    assert table["rows"][-1]["planned_qty"] == 10
    assert all("unit" in row for row in table["rows"])


def test_table_compiler_keeps_full_rows_when_columns_filtered():
    spec = PresentationSpec(
        view="table",
        fields=("product_code", "planned_qty"),
        table=PresentationTableSpec(hidden_fields=("warehouse",)),
    )
    rows = _rows()
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [
                {"key": "product_code"},
                {"key": "warehouse"},
                {"key": "planned_qty"},
            ],
            "rows": rows,
        }
    }
    PresentationTableCompilerService.apply(
        metadata,
        spec=spec,
        labels={},
        formats={},
    )
    table = metadata["tablePresentation"]
    assert {col["key"] for col in table["columns"]} == {"product_code", "planned_qty"}
    assert len(table["rows"]) == len(rows)
    for original, compiled in zip(rows, table["rows"]):
        assert original == compiled


def test_table_view_does_not_invent_chart_slot():
    spec = PresentationSpec(view="table", fields=("product_code", "planned_qty"))
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": "product_code"}, {"key": "planned_qty"}],
            "rows": _rows(),
        }
    }
    profile = PresentationDataProfile(row_count=3, sampled_row_count=3)
    PresentationSpecCompilerService.compile_into_metadata(
        metadata,
        spec=spec,
        profile=profile,
    )
    assert metadata.get("chartPresentation") is None
