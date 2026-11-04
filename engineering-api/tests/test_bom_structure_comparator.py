"""DEC-VAL-022 §18 — comparador puro desenho × BOM por ocorrência.

Fixtures reproduzem o shape real de ``component_table.rows``
(drawing_understanding.v1, células tipadas) e de
``flatten_bom_occurrences``. Ground truth explícito — o caso canônico
reproduz a topologia observada de 90263520 (5 PI no desenho × 4 PI na
BOM vigente) sem hardcode do código no comparador.
"""

from __future__ import annotations

from engineering_app.application.drawing.bom_structure_comparator import (
    compare_bom_to_drawing,
)

PRODUCT = "90263520"


def _row(code, y, *, desc=None, qty=None, page=1):
    cells = [
        {
            "text": code,
            "col": 0,
            "row": y,
            "col_type": "component_code",
            "bounding_box_px": [10, y, 60, y + 8],
            "page": page,
        }
    ]
    return {
        "row": y,
        "y_px": float(y),
        "component_code": code,
        "description": desc,
        "quantity": qty,
        "cells": cells,
    }


def _table(rows, *, candidate=True, unreliable=False):
    return {
        "candidate": candidate,
        "rows": rows,
        "row_count": len(rows),
        "code_count": sum(1 for r in rows if r.get("component_code")),
        "unreliable_boundary": unreliable,
    }


def _bom(*occs):
    out = []
    for i, (code, parent, depth) in enumerate(occs):
        out.append(
            {
                "occurrence_id": f"O{i + 1:04d}",
                "component_code": code,
                "component_type": "PI" if code.startswith("5") else "MP",
                "parent_code": parent,
                "depth": depth,
                "path": f"{PRODUCT}/{code}" if depth == 1 else code,
                "quantity_raw": 1,
                "unit_raw": "PC",
            }
        )
    return out


def _tokens(*codes, page=1):
    return [{"normalized_text": c, "page": page} for c in codes]


# --- caso canônico 90263520 ---------------------------------------------------


def test_canonical_90263520_drawing_only():
    """5 PI no desenho × 4 PI na BOM → DRAWING_ONLY do excedente."""
    table = _table(
        [
            _row("50213064", 10),
            _row("10400040", 20),
            _row("50230890", 30),
            _row("10400040", 40),
            _row("50230893", 50),
            _row("10080063", 60),
            _row("50232466", 70),
            _row("50232467", 80),
        ]
    )
    bom = _bom(
        ("50230890", PRODUCT, 1),
        ("50230893", PRODUCT, 1),
        ("50232466", PRODUCT, 1),
        ("50232467", PRODUCT, 1),
        ("10400040", "50230890", 2),
        ("10400040", "50230893", 2),
        ("10080063", "50230893", 2),
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50213064"),
        drawing_pages=1,
    )
    assert out["status"] == "DIVERGENCES_CANDIDATES"
    drawing_only = [
        f for f in out["findings"] if f["type"] == "DRAWING_ONLY"
    ]
    assert [f["item_code"] for f in drawing_only] == ["50213064"]
    f = drawing_only[0]
    assert f["review_status"] == "PENDING_HUMAN_REVIEW"
    assert f["parent_code"] == PRODUCT
    assert (
        f["evidence"]["bom_relationship"] == "ABSENT_IN_CURRENT_STRUCTURE"
    )
    assert f["evidence"]["drawing_page"] == 1
    # MPs compartilhadas por outros conjuntos não viram ausência global.
    bom_only = [f for f in out["findings"] if f["type"] == "BOM_ONLY"]
    assert not bom_only
    assert out["counts"]["matched_occurrences"] >= 6


def test_merged_ocr_cell_yields_distinct_codes():
    """OCR pode fundir códigos num campo: cada código vira ocorrência.

    Shape real observado no pipeline: component_code da linha chega como
    ``"a 50213064 90263520 50230890"`` — três códigos distintos."""
    row = {
        "row": 0,
        "y_px": 10.0,
        "component_code": "a 50213064 90263520 50230890",
        "description": None,
        "quantity": "cf20verm-00042/11/03-0000-0000",
        "cells": [
            {"text": "a 50213064 90263520 50230890",
             "col": 0, "row": 0, "col_type": "component_code"},
        ],
    }
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=_bom(
            ("50230890", PRODUCT, 1),
            ("50230893", PRODUCT, 1),
            ("50232466", PRODUCT, 1),
            ("50232467", PRODUCT, 1),
        ),
        component_table=_table([row] + [
            _row("50230893", 20), _row("50232466", 30),
            _row("50232467", 40),
        ]),
        tokens=_tokens("50213064"),
    )
    drawing_only = [
        f for f in out["findings"] if f["type"] == "DRAWING_ONLY"
    ]
    assert [f["item_code"] for f in drawing_only] == ["50213064"]
    assert out["counts"]["matched_occurrences"] == 4


def test_bom_only_when_full_coverage():
    table = _table([_row("50000001", 10)])
    bom = _bom(("50000001", PRODUCT, 1), ("50000002", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001"),
    )
    types = {f["type"] for f in out["findings"]}
    assert "BOM_ONLY" in types
    f = next(f for f in out["findings"] if f["type"] == "BOM_ONLY")
    assert f["item_code"] == "50000002"
    assert f["level"] == 1


def test_multiple_divergences():
    table = _table(
        [_row("50000001", 10), _row("50000003", 20), _row("50000009", 30)]
    )
    bom = _bom(("50000001", PRODUCT, 1), ("50000002", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001"),
    )
    assert out["status"] == "DIVERGENCES_CANDIDATES"
    codes = {(f["type"], f["item_code"]) for f in out["findings"]}
    assert ("DRAWING_ONLY", "50000003") in codes
    assert ("DRAWING_ONLY", "50000009") in codes
    assert ("BOM_ONLY", "50000002") in codes


def test_same_code_under_different_parent_flagged():
    """Código presente nos dois lados mas sob pais verificados distintos."""
    table = _table(
        [
            _row("50000001", 10),
            _row("10400040", 20),
        ]
    )
    bom = _bom(
        ("50000001", PRODUCT, 1),
        ("50000002", PRODUCT, 1),
        ("10400040", "50000002", 2),
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("10400040", "50000002"),
    )
    kinds = {f["type"] for f in out["findings"]}
    assert "PARENT_RELATION_MISMATCH" in kinds
    f = next(
        f
        for f in out["findings"]
        if f["type"] == "PARENT_RELATION_MISMATCH"
    )
    assert f["evidence"]["bom_parents"] == ["50000002"]


def test_repeated_code_same_parent_is_occurrence_match():
    table = _table(
        [
            _row("50000001", 10),
            _row("10400040", 20),
            _row("10400040", 30),
        ]
    )
    bom = _bom(
        ("50000001", PRODUCT, 1),
        ("10400040", "50000001", 2),
        ("10400040", "50000001", 2),
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001", "10400040"),
    )
    assert out["status"] == "NO_DIVERGENCE_DETECTED"
    assert out["counts"]["matched_occurrences"] == 3


def test_unknown_parent_matches_by_code_with_limitation():
    """Linha sem grupo PI aberto → match por código + limitation."""
    table = _table([_row("10400040", 10)])
    bom = _bom(("10400040", "50000001", 2))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("10400040"),
    )
    assert out["status"] == "BOM_ONLY" or out["status"] in {
        "NO_DIVERGENCE_DETECTED",
        "DIVERGENCES_CANDIDATES",
        "INCONCLUSIVE",
    }
    assert out["counts"]["matched_occurrences"] == 1
    assert any("parent_relation_unverified" in l for l in out["limitations"])
    bom_only = [f for f in out["findings"] if f["type"] == "BOM_ONLY"]
    assert not bom_only  # mesma BOM occurrence foi consumida pelo match


def test_table_on_page_two():
    table = _table([_row("50000001", 10, page=2)])
    bom = _bom(("50000001", PRODUCT, 1), ("50000002", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001", page=2),
        drawing_pages=2,
    )
    assert 2 in (out["coverage"]["analyzed_pages"] or [])
    bom_only = [f for f in out["findings"] if f["type"] == "BOM_ONLY"]
    assert bom_only and bom_only[0]["item_code"] == "50000002"


def test_partial_extraction_is_inconclusive():
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=_bom(("50000001", PRODUCT, 1)),
        component_table={"candidate": False, "rows": [], "row_count": 0},
        tokens=None,
    )
    assert out["status"] == "INCONCLUSIVE"
    assert not out["findings"]
    assert any("drawing_table_unread" in l for l in out["limitations"])


def test_no_table_no_false_bom_only():
    """Sem tabela lida: nenhum BOM_ONLY — ausência não declarada."""
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=_bom(("50000001", PRODUCT, 1)),
        component_table=None,
        tokens=None,
    )
    assert out["status"] == "INCONCLUSIVE"
    assert all(f["type"] != "BOM_ONLY" for f in out["findings"])


def test_unreliable_boundary_blocks_bom_only():
    table = _table([_row("50000001", 10)], unreliable=True)
    bom = _bom(("50000001", PRODUCT, 1), ("50000002", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001"),
    )
    assert all(f["type"] != "BOM_ONLY" for f in out["findings"])
    assert out["status"] == "INCONCLUSIVE" or any(
        "bom_only_unverified" in l for l in out["limitations"]
    )


def test_bom_unavailable_is_inconclusive():
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=None,
        component_table=_table([_row("50000001", 10)]),
        tokens=None,
        bom_error={"code": "forbidden", "status_code": 403},
    )
    assert out["status"] == "INCONCLUSIVE"
    assert not out["findings"]
    assert out["coverage"]["bom_available"] is False


def test_full_match_no_divergence():
    table = _table(
        [_row("50000001", 10), _row("10400040", 20)]
    )
    bom = _bom(
        ("50000001", PRODUCT, 1), ("10400040", "50000001", 2)
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001", "10400040"),
    )
    assert out["status"] == "NO_DIVERGENCE_DETECTED"
    assert out["counts"]["divergences"] == 0


def test_bom_code_visible_outside_cells_not_bom_only():
    """Código BOM visível no doc fora das células tipadas → unclassified."""
    table = _table([_row("50000001", 10)])
    bom = _bom(("50000001", PRODUCT, 1), ("50000002", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001", "50000002"),
    )
    assert all(f["type"] != "BOM_ONLY" for f in out["findings"])
    # presença por token (não tipado) conta como match, com limitation
    assert out["counts"]["matched_occurrences"] == 2
    assert any("presence_by_token_only" in l for l in out["limitations"])


def test_quantities_never_compared_without_rule():
    table = _table([_row("50000001", 10, qty="1")])
    bom = _bom(("50000001", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001"),
    )
    assert all(f["type"] != "QTY_MISMATCH" for f in out["findings"])
    assert any(
        "quantitative_comparison: INCONCLUSIVE" in l
        for l in out["limitations"]
    )
