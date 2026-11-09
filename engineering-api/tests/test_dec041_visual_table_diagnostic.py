"""DEC-VAL-041 — diagnostic fixtures (updated by DEC-VAL-042 gate policy).

Proves the first defective boundary for product 90264026 class and the
remediation: SLANet cells separate group identity from component code;
localized ``span_conflict`` no longer forces fallback fusion when native
associations are usable.
"""
from __future__ import annotations

from engineering_app.application.drawing.understanding import (
    apply_native_table_observations,
    rows_from_native_cells,
)


def _bbox(x0: float, y0: float, x1: float, y1: float) -> list[float]:
    return [x0, y0, x1, y0, x1, y1, x0, y1]


def _cell(
    row: int,
    col: int,
    text: str,
    *,
    rowspan: int = 1,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    page: int = 1,
) -> dict:
    return {
        "row": row,
        "col": col,
        "rowspan": rowspan,
        "colspan": 1,
        "text": text,
        "page": page,
        "bounding_box_px": _bbox(x0, y0, x1, y1),
        "token_centers": [[(x0 + x1) / 2.0, (y0 + y1) / 2.0]],
    }


# Minimal native grade mirroring the measured 90264026 table band.
NATIVE_90264026_CELLS = [
    _cell(0, 0, "90264026 CHCIOTE DE LIGACAO", x0=60, y0=1546, x1=290, y1=1678),
    _cell(0, 2, "A", rowspan=3, x0=370, y0=1570, x1=400, y1=1590),
    _cell(0, 5, "1", x0=420, y0=1570, x1=450, y1=1590),
    _cell(0, 6, "10080001", x0=480, y0=1570, x1=560, y1=1590),
    _cell(0, 7, "TERM. BANDEIRA", x0=600, y0=1570, x1=900, y1=1590),
    _cell(1, 2, "F", x0=370, y0=1600, x1=400, y1=1620),
    _cell(1, 5, "1", x0=420, y0=1600, x1=450, y1=1620),
    _cell(1, 6, "10081047", x0=480, y0=1600, x1=560, y1=1620),
    _cell(1, 7, "TERM. OLHAL", x0=600, y0=1600, x1=900, y1=1620),
    _cell(3, 3, "B", x0=370, y0=1635, x1=400, y1=1655),
    _cell(3, 4, "1", x0=420, y0=1635, x1=450, y1=1655),
    _cell(3, 5, "10090010", x0=480, y0=1635, x1=560, y1=1655),
    _cell(3, 6, "ISOLADOR NYLON 90", x0=600, y0=1635, x1=900, y1=1655),
    _cell(4, 3, "C", x0=370, y0=1665, x1=400, y1=1685),
    _cell(4, 4, "1", x0=420, y0=1665, x1=450, y1=1685),
    _cell(4, 5, "10110020", x0=480, y0=1665, x1=560, y1=1685),
    _cell(4, 6, "ETIQUETA ACETATO", x0=600, y0=1665, x1=900, y1=1685),
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


def test_structure_inconsistent_span_conflict_now_tolerates_usable_native():
    """DEC-VAL-041 boundary; remediated by DEC-VAL-042 gate policy."""
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
    by_item = {
        str(r.get("item") or "").upper(): r
        for r in rows
        if r.get("item")
    }
    assert by_item["B"].get("component_code") == "10090010"
    limitations = " ".join(updated.get("limitations") or [])
    assert "table_perception:span_conflict_tolerated" in limitations
    assert "structure_incomplete" not in limitations


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
    invented = "99999999"
    assert not any(invented in text for text in observed_texts)
