"""DEC-VAL-043 — preservação de associações sob grade nativa parcial."""
from __future__ import annotations

from engineering_app.application.drawing.understanding import (
    apply_native_table_observations,
    native_cells_preferable,
    reconcile_native_and_fallback_rows,
)


def _bbox(x0, y0, x1, y1):
    return [x0, y0, x1, y0, x1, y1, x0, y1]


def _cell(row, col, text, *, x0, y0, x1, y1, rowspan=1):
    return {
        "row": row,
        "col": col,
        "rowspan": rowspan,
        "colspan": 1,
        "text": text,
        "page": 1,
        "bounding_box_px": _bbox(x0, y0, x1, y1),
        "token_centers": [[(x0 + x1) / 2.0, (y0 + y1) / 2.0]],
    }


def _fb(item, qty, code, desc=None):
    return {
        "page": 1,
        "item": item,
        "quantity": qty,
        "component_code": code,
        "description": desc,
        "association_status": "FIELD_IDENTIFIED",
        "topology_source": "token_cluster",
    }


# Nativa recupera A/B com códigos; F/G só como âncoras de banda-X de
# item (sem código) — cobertura usável < fallback rico em C/D/E.
PARTIAL_NATIVE_CELLS = [
    _cell(0, 0, "90264026 CHCIOTE DE LIGACAO", x0=60, y0=10, x1=200, y1=120),
    _cell(0, 2, "A", x0=300, y0=20, x1=330, y1=40),
    _cell(0, 3, "1", x0=350, y0=20, x1=380, y1=40),
    _cell(0, 4, "10080001", x0=400, y0=20, x1=480, y1=40),
    _cell(0, 5, "TERM. BANDEIRA", x0=500, y0=20, x1=700, y1=40),
    _cell(1, 2, "F", x0=300, y0=50, x1=330, y1=70),
    _cell(2, 2, "B", x0=300, y0=80, x1=330, y1=100),
    _cell(2, 3, "1", x0=350, y0=80, x1=380, y1=100),
    _cell(2, 4, "10090010", x0=400, y0=80, x1=480, y1=100),
    _cell(2, 5, "ISOLADOR NYLON 90", x0=500, y0=80, x1=700, y1=100),
    _cell(3, 2, "G", x0=300, y0=110, x1=330, y1=130),
    _cell(4, 2, "H", x0=300, y0=140, x1=330, y1=160),
]


def test_partial_native_must_not_drop_fallback_unique_associations():
    """NO_SILENT_ASSOCIATION_LOSS — RED histórico da DEC-042, GREEN agora."""
    fallback = [
        _fb("A", "1", "10080001", "DESC_A_FALLBACK"),
        _fb("B", "1", "90264026 10090010", None),
        _fb("C", "6", "10081389", "DESC_C_KEEP"),
        _fb("D", "3", "10081685", "DESC_D_KEEP"),
        _fb("E", "2", "10091368", "DESC_E_KEEP"),
    ]
    # Preferência: nativa tem menos usáveis que fallback → parcial
    apply, reason = native_cells_preferable(
        consistent=False,
        structure_limitations=["span_conflict"],
        native_rows=[
            {"item": "A", "component_code": "10080001", "description": "NA"},
            {"item": "B", "component_code": "10090010", "description": "ISOLADOR"},
            {"item": "G", "component_code": "10110679", "description": "NG"},
        ],
        fallback_rows=fallback,
    )
    assert apply is True
    assert reason == "span_conflict_tolerated_partial"

    updated = apply_native_table_observations(
        {
            "component_table": {"rows": list(fallback), "row_count": 5},
            "limitations": [],
        },
        [{
            "region_type": "component_table",
            "page": 1,
            "result": {
                "cells": PARTIAL_NATIVE_CELLS,
                "tables": [{
                    "structure_consistent": False,
                    "structure_limitations": ["span_conflict"],
                }],
            },
        }],
    )
    rows = (updated.get("component_table") or {}).get("rows") or []
    by_item = {
        str(r.get("item") or "").upper(): r for r in rows if r.get("item")
    }
    assert by_item["B"]["component_code"] == "10090010"
    assert "ISOLADOR" in str(by_item["B"].get("description") or "")
    assert "90264026" not in str(by_item["B"]["component_code"])
    # Associações fallback sustentadas preservadas
    assert by_item["C"]["component_code"] == "10081389"
    assert by_item["C"]["description"] == "DESC_C_KEEP"
    assert by_item["D"]["component_code"] == "10081685"
    assert by_item["E"]["component_code"] == "10091368"
    lim = " ".join(updated.get("limitations") or [])
    assert "span_conflict_tolerated_partial" in lim


def test_full_replace_when_native_coverage_sufficient():
    fallback = [_fb("B", "1", "90264026 10090010", None)]
    native = [
        {"item": "A", "component_code": "10080001", "description": "DA"},
        {"item": "B", "component_code": "10090010", "description": "ISOLADOR"},
    ]
    apply, reason = native_cells_preferable(
        consistent=False,
        structure_limitations=["span_conflict"],
        native_rows=native,
        fallback_rows=fallback,
    )
    assert apply is True
    assert reason == "span_conflict_tolerated"
    out = reconcile_native_and_fallback_rows(
        native_rows=native,
        fallback_rows=fallback,
        page=1,
        mode="replace",
    )
    assert len(out) == 2
    assert {r["item"] for r in out} == {"A", "B"}


def test_negative_no_indiscriminate_merge_on_duplicate_items():
    """Itens repetidos não são chave de merge — preserva fallback."""
    fallback = [
        _fb("A9", "2", "10080065", "G1"),
        _fb("A9", "6", "10080065", "G2"),
    ]
    native = [
        {"item": "A9", "component_code": "10080065", "description": "ONLY_ONE"},
        {"item": "B", "component_code": "10090010", "description": "X"},
    ]
    out = reconcile_native_and_fallback_rows(
        native_rows=native,
        fallback_rows=fallback,
        page=1,
        mode="preserve",
    )
    a9 = [r for r in out if str(r.get("item") or "").upper() == "A9"]
    assert len(a9) == 2
    assert {r.get("description") for r in a9} == {"G1", "G2"}


def test_negative_group_description_not_promoted_on_partial_upgrade():
    fallback = [
        _fb("B", "1", "90264026 10090010", None),
        _fb("C", "6", "10081389", "KEEP"),
    ]
    native = [
        {
            "item": "B",
            "component_code": "10090010",
            "description": "ISOLADOR NYLON",
        },
    ]
    out = reconcile_native_and_fallback_rows(
        native_rows=native,
        fallback_rows=fallback,
        page=1,
        mode="preserve",
    )
    by_item = {str(r["item"]).upper(): r for r in out}
    assert "CHICOTE" not in str(by_item["B"].get("description") or "")
    assert by_item["C"]["description"] == "KEEP"
