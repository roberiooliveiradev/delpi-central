"""DEC-VAL-041 — diagnostic fixtures (investigation only).

Proves the first defective boundary for product 90264026 class:
SLANet cells can separate group identity from component code, but
``structure_consistent=false`` (span_conflict) causes
``apply_native_table_observations`` to discard the native grade and
keep the fallback token grouping that fuses codes.

No production association logic is changed here.
"""
from __future__ import annotations

from engineering_app.application.drawing.understanding import (
    apply_native_table_observations,
    rows_from_native_cells,
)


def _cell(
    row: int,
    col: int,
    text: str,
    *,
    rowspan: int = 1,
    colspan: int = 1,
    page: int = 1,
) -> dict:
    return {
        "row": row,
        "col": col,
        "rowspan": rowspan,
        "colspan": colspan,
        "text": text,
        "page": page,
        "bbox": [float(col), float(row), float(col) + 1, float(row) + 1],
    }


# Minimal native grade mirroring the measured 90264026 table band:
# group identity shares a left cell; item B code is a separate cell.
NATIVE_90264026_CELLS = [
    _cell(0, 0, "90264026 CHCIOTE DE LIGACAO"),
    _cell(0, 2, "A", rowspan=3),
    _cell(0, 5, "1"),
    _cell(0, 6, "10080001"),
    _cell(0, 7, "TERM. BANDEIRA"),
    _cell(3, 3, "B"),
    _cell(3, 4, "1"),
    _cell(3, 5, "10090010"),
    _cell(3, 6, "ISOLADOR NYLON 90"),
]


def test_native_cells_keep_group_code_separate_from_item_b():
    rows, _ = rows_from_native_cells(NATIVE_90264026_CELLS, page=1)
    by_item = {
        str(r.get("item") or "").upper(): r
        for r in rows
        if r.get("item")
    }
    assert "B" in by_item
    code = str(by_item["B"].get("component_code") or "")
    assert code == "10090010"
    assert "90264026" not in code


def test_structure_inconsistent_gate_preserves_fallback_fusion():
    """FIRST_DEFECTIVE_BOUNDARY for 90264026 class — PROVEN in fixture.

    When SLANet reports structure_consistent=false, native rows are not
    applied and the prior fallback row (fused codes) remains published.
    """
    fallback_rows = [
        {
            "page": 1,
            "item": "B",
            "quantity": "1",
            "component_code": "90264026 10090010",
            "description": None,
            "association_status": "FIELD_IDENTIFIED",
        }
    ]
    understanding = {
        "component_table": {"rows": list(fallback_rows), "row_count": 1},
        "limitations": [],
    }
    observations = [
        {
            "region_type": "component_table",
            "page": 1,
            "result": {
                "cells": NATIVE_90264026_CELLS,
                "tables": [
                    {
                        "structure_consistent": False,
                        "structure_limitations": ["span_conflict"],
                    }
                ],
                "limitations": ["span_conflict"],
            },
        }
    ]
    updated = apply_native_table_observations(understanding, observations)
    rows = (updated.get("component_table") or {}).get("rows") or []
    assert len(rows) == 1
    assert rows[0].get("component_code") == "90264026 10090010"
    limitations = " ".join(updated.get("limitations") or [])
    assert "table_perception:structure_incomplete" in limitations


def test_consistent_native_observation_replaces_fused_fallback():
    """Counterfactual: same cells with consistent=true recover item B."""
    fallback_rows = [
        {
            "page": 1,
            "item": "B",
            "quantity": "1",
            "component_code": "90264026 10090010",
            "description": None,
            "association_status": "FIELD_IDENTIFIED",
        }
    ]
    understanding = {
        "component_table": {"rows": list(fallback_rows), "row_count": 1},
        "limitations": [],
    }
    observations = [
        {
            "region_type": "component_table",
            "page": 1,
            "result": {
                "cells": NATIVE_90264026_CELLS,
                "tables": [{"structure_consistent": True}],
                "limitations": [],
            },
        }
    ]
    updated = apply_native_table_observations(understanding, observations)
    rows = (updated.get("component_table") or {}).get("rows") or []
    by_item = {
        str(r.get("item") or "").upper(): r
        for r in rows
        if r.get("item")
    }
    assert by_item["B"].get("component_code") == "10090010"
    assert (updated.get("component_table") or {}).get(
        "topology_source"
    ) == "native_table_cells"


def test_stage_d_hypothesis_revalidation_without_invented_tokens():
    """IA-proponent / framework-verifier offline pattern.

    A geometric hypothesis that says 'prefer native cells despite
    span_conflict' is accepted only if every referenced token text
    already exists in the perception cells, then revalidated by
    rows_from_native_cells — no parallel parser.
    """
    hypothesis = {
        "hypothesis_type": "PREFER_NATIVE_CELLS_DESPITE_SPAN_CONFLICT",
        "region_ref": "90264026:p1:component_table",
        "token_refs": ["90264026", "10090010", "B"],
        "proposed_grouping": [
            {"role": "group_context", "text": "90264026 CHCIOTE DE LIGACAO"},
            {"role": "item_row", "item": "B", "component_code": "10090010"},
        ],
        "evidence_state": "CANDIDATE",
    }
    observed_texts = {
        (c.get("text") or "") for c in NATIVE_90264026_CELLS
    }
    for ref in hypothesis["token_refs"]:
        assert any(ref in text for text in observed_texts), ref

    rows, _ = rows_from_native_cells(NATIVE_90264026_CELLS, page=1)
    b = next(r for r in rows if str(r.get("item") or "").upper() == "B")
    assert b.get("component_code") == "10090010"
    # Reject invented token
    invented = "99999999"
    assert not any(invented in text for text in observed_texts)
