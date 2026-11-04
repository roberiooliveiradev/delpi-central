"""RQ-VAL-027/028/029 — regiões documentais, hierarquia multinível e
cobertura multipágina do comparador desenho × BOM.

Ground truth sintético — nenhum código real é hardcoded na regra."""
from __future__ import annotations

from engineering_app.application.drawing.bom_structure_comparator import (
    compare_bom_to_drawing,
)

PRODUCT = "90264017"


def _row(code, y, *, desc=None, qty=None, page=1, col=0,
         col_type="component_code"):
    cells = [
        {
            "text": code,
            "col": col,
            "row": y,
            "col_type": col_type,
            "bounding_box_px": [10 + col * 100, y, 60 + col * 100, y + 8],
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
        "page": page,
    }


def _two_col_row(set_code, item_code, y, *, page=1):
    """Linha de tabela com coluna de conjuntos (col 0) + coluna de
    itens (col 1) — layout DELPI real de desenho multipágina."""
    return {
        "row": y,
        "y_px": float(y),
        "page": page,
        "col_types": {"0": "component_code", "1": "component_code"},
        "cells": [
            {
                "text": set_code, "col": 0, "row": y,
                "col_type": "component_code", "page": page,
                "bounding_box_px": [10, y, 60, y + 8],
            },
            {
                "text": item_code, "col": 1, "row": y,
                "col_type": "component_code", "page": page,
                "bounding_box_px": [120, y, 180, y + 8],
            },
        ],
    }


def _item_only_row(item_code, y, *, page=1):
    """Linha sem código na coluna de conjuntos — membro de conjunto
    por célula mesclada/continuação (set_span)."""
    return {
        "row": y,
        "y_px": float(y),
        "page": page,
        "col_types": {"0": "component_code", "1": "component_code"},
        "cells": [
            {
                "text": item_code, "col": 1, "row": y,
                "col_type": "component_code", "page": page,
                "bounding_box_px": [120, y, 180, y + 8],
            },
        ],
    }


def _table(rows, *, candidate=True, unreliable=False):
    return {
        "candidate": candidate,
        "rows": rows,
        "row_count": len(rows),
        "code_count": sum(
            len(c.get("cells") or []) for c in rows
        ),
        "unreliable_boundary": unreliable,
    }


def _bom(product, *occs):
    out = []
    for i, (code, parent, depth) in enumerate(occs):
        out.append(
            {
                "occurrence_id": f"O{i + 1:04d}",
                "component_code": code,
                "component_type": (
                    "PI" if code.startswith("5")
                    else "PA" if code.startswith("7")
                    else "MP"
                ),
                "parent_code": parent,
                "depth": depth,
                "path": f"{product}/{code}" if depth == 1 else code,
                "quantity_raw": 1,
                "unit_raw": "PC",
            }
        )
    return out


def _tokens(*codes, page=1):
    return [{"normalized_text": c, "page": page} for c in codes]


def _ctx(code, region, page=1):
    return {"code": code, "region": region, "page": page}


# --- RQ-VAL-027: regiões documentais -------------------------------------------


def test_revision_history_code_never_drawing_only():
    """Caso canônico 90264017: código substituído citado apenas no
    histórico de revisão → evidência contextual, não DRAWING_ONLY."""
    table = _table([_row("10080438", 10, page=2)])
    bom = _bom(PRODUCT, ("10080438", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("10080438", page=2),
        drawing_pages=14,
        code_contexts=[
            _ctx("10080438", "component_table", 2),
            _ctx("10080535", "revision_history", 2),
            _ctx("10080438", "revision_history", 2),
        ],
    )
    assert all(
        f["item_code"] != "10080535" for f in out["findings"]
    )
    assert out["counts"]["contextual_codes"] == 1
    ctx = out["contextual_codes"][0]
    assert ctx["code"] == "10080535"
    assert ctx["regions"] == ["revision_history"]
    assert any("contextual_code_mentions" in l for l in out["limitations"])
    # código vigente citado no histórico segue comparável via tabela
    assert out["counts"]["matched_occurrences"] == 1


def test_historical_code_also_in_current_table_both_preserved():
    """R4: código no histórico E na tabela vigente — evidências
    separadas, ocorrência tipada comparável."""
    table = _table([_row("50000001", 10)])
    bom = _bom(PRODUCT, ("50000001", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001"),
        code_contexts=[
            _ctx("50000001", "component_table"),
            _ctx("50000001", "revision_history"),
        ],
    )
    assert out["counts"]["matched_occurrences"] == 1


def test_note_region_code_not_presence():
    """R3: código citado só em nota técnica não é presença — BOM
    occurrence permanece não verificada (não consome match)."""
    table = _table([_row("50000001", 10)])
    bom = _bom(
        PRODUCT,
        ("50000001", PRODUCT, 1),
        ("50000002", PRODUCT, 1),
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001"),
        code_contexts=[
            _ctx("50000001", "component_table"),
            _ctx("50000002", "notes"),
        ],
    )
    assert out["counts"]["matched_occurrences"] == 1
    assert out["counts"]["contextual_codes"] == 1
    assert out["contextual_codes"][0]["code"] == "50000002"


def test_title_block_code_not_presence():
    table = _table([_row("50000001", 10)])
    bom = _bom(
        PRODUCT,
        ("50000001", PRODUCT, 1),
        ("50000002", PRODUCT, 1),
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001"),
        code_contexts=[
            _ctx("50000001", "component_table"),
            _ctx("50000002", "title_block"),
        ],
    )
    assert out["counts"]["contextual_codes"] == 1


def test_drawing_area_code_still_presence_only():
    """Região comparável-adjacente (drawing_area) segue presença por
    token — preserva comportamento vigente fail-closed."""
    table = _table([_row("50000001", 10)])
    bom = _bom(
        PRODUCT,
        ("50000001", PRODUCT, 1),
        ("50000002", PRODUCT, 1),
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001", "50000002"),
        code_contexts=[
            _ctx("50000001", "component_table"),
            _ctx("50000002", "drawing_area"),
        ],
    )
    assert out["counts"]["matched_occurrences"] == 2
    assert out["counts"]["contextual_codes"] == 0


def test_drawing_only_requires_page_provenance():
    """R7: DRAWING_ONLY sem página comprovável degrada a inconclusivo."""
    row = _row("50000099", 10)
    for c in row["cells"]:
        c.pop("page", None)
    row.pop("page", None)
    table = _table([_row("50000001", 20, page=2), row])
    bom = _bom(PRODUCT, ("50000001", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001", page=2),
        code_contexts=[_ctx("50000001", "component_table", 2)],
    )
    assert all(
        f["item_code"] != "50000099" for f in out["findings"]
    )
    assert any(
        "unprovenanced_drawing_occurrence" in l
        for l in out["limitations"]
    )
    assert out["counts"]["unprovenanced_occurrences"] == 1


def test_drawing_only_with_page_evidence_preserved():
    """Finding legítimo mantém proveniência página/região/linha."""
    table = _table([_row("50213064", 10, page=3)])
    bom = _bom(PRODUCT, ("50230890", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50213064", page=3),
    )
    f = next(
        f for f in out["findings"] if f["type"] == "DRAWING_ONLY"
    )
    assert f["item_code"] == "50213064"
    assert f["evidence"]["drawing_page"] == 3
    assert f["evidence"]["drawing_region"] == "component_table"


# --- RQ-VAL-028: hierarquia multinível ------------------------------------------


def test_set_column_membership_matches_bom():
    """Caso canônico 90264030: PI na coluna de itens sob PA na coluna
    de conjuntos — relação real preservada, sem falso mismatch."""
    table = _table([
        _two_col_row("70260010", "50225512", 10, page=2),
    ])
    bom = _bom(
        "90264030",
        ("70260010", "90264030", 1),
        ("50225512", "70260010", 2),
    )
    out = compare_bom_to_drawing(
        product_code="90264030",
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("70260010", "50225512", page=2),
    )
    assert all(
        f["type"] != "PARENT_RELATION_MISMATCH" for f in out["findings"]
    )
    assert out["counts"]["matched_occurrences"] == 2


def test_set_span_inherits_merged_conjunto():
    """Célula mesclada: linhas seguintes sem código de conjunto
    herdam a âncora de conjunto ativa (set_span) para matching."""
    table = _table([
        _two_col_row("70260010", "50225510", 10, page=2),
        _item_only_row("50225512", 20, page=2),
        _item_only_row("10440001", 30, page=2),
    ])
    bom = _bom(
        "90264030",
        ("70260010", "90264030", 1),
        ("50225510", "70260010", 2),
        ("50225512", "70260010", 2),
        ("10440001", "50225512", 3),
    )
    out = compare_bom_to_drawing(
        product_code="90264030",
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("70260010", "50225510", "50225512", "10440001",
                       page=2),
    )
    assert all(
        f["type"] != "PARENT_RELATION_MISMATCH" for f in out["findings"]
    )
    assert out["counts"]["matched_occurrences"] == 4


def test_set_span_divergence_unverified_not_finding():
    """Célula mesclada com pai divergente da BOM → unverified, nunca
    finding — continuação de conjunto pode ser célula vazia."""
    table = _table([
        _two_col_row("70260010", "50225510", 10),
        _item_only_row("50225512", 20),
    ])
    bom = _bom(
        "90264030",
        ("70260010", "90264030", 1),
        ("50225510", "70260010", 2),
        ("50225512", "90264030", 1),
    )
    out = compare_bom_to_drawing(
        product_code="90264030",
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("70260010", "50225510", "50225512"),
    )
    assert all(
        f["type"] != "PARENT_RELATION_MISMATCH" for f in out["findings"]
    )


def test_set_member_same_row_divergence_unverified():
    """Mesmo pai conjunto explícito na linha divergindo da BOM →
    evidência registrada, não mismatch fabricado (R4/R7)."""
    table = _table([
        _two_col_row("70260010", "50225512", 10),
    ])
    bom = _bom(
        "90264030",
        ("70260010", "90264030", 1),
        ("50225512", "90264030", 1),
    )
    out = compare_bom_to_drawing(
        product_code="90264030",
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("70260010", "50225512"),
    )
    assert all(
        f["type"] != "PARENT_RELATION_MISMATCH" for f in out["findings"]
    )
    assert any(
        "unverified_parent_relations" in l for l in out["limitations"]
    )


def test_repeated_code_in_distinct_sets():
    """R8: mesmo código em conjuntos distintos — ocorrências
    preservadas com pais próprios."""
    table = _table([
        _two_col_row("70260010", "10440001", 10),
        _two_col_row("70260020", "10440001", 20),
    ])
    bom = _bom(
        "90264030",
        ("70260010", "90264030", 1),
        ("70260020", "90264030", 1),
        ("10440001", "70260010", 2),
        ("10440001", "70260020", 2),
    )
    out = compare_bom_to_drawing(
        product_code="90264030",
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("70260010", "70260020", "10440001"),
    )
    # Pais dos conjuntos não demonstrados pela tabela — matched por
    # código, relações não verificadas declaradas: INCONCLUSIVE honesto.
    assert out["status"] == "INCONCLUSIVE"
    assert out["counts"]["matched_occurrences"] == 4
    assert all(
        f["type"] != "PARENT_RELATION_MISMATCH" for f in out["findings"]
    )


def test_root_anchor_still_flags_real_mismatch():
    """Item tipado como raiz (coluna de conjuntos única) divergente da
    BOM segue candidato a mismatch — proteção preservada."""
    table = _table([_row("50090001", 10)])
    bom = _bom(
        PRODUCT,
        ("90350410", PRODUCT, 1),
        ("50090001", "90350410", 2),
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50090001"),
    )
    mismatch = [
        f for f in out["findings"]
        if f["type"] == "PARENT_RELATION_MISMATCH"
    ]
    assert mismatch and mismatch[0]["item_code"] == "50090001"


def test_three_level_hierarchy():
    """Três níveis: PA raiz → PI intermediário → MP filho."""
    table = _table([
        _two_col_row("70260010", "50225510", 10),
        _item_only_row("10440001", 20),
    ])
    bom = _bom(
        "90264030",
        ("70260010", "90264030", 1),
        ("50225510", "70260010", 2),
        ("10440001", "50225510", 3),
    )
    out = compare_bom_to_drawing(
        product_code="90264030",
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("70260010", "50225510", "10440001"),
    )
    assert out["counts"]["matched_occurrences"] == 3
    assert all(
        f["type"] != "PARENT_RELATION_MISMATCH" for f in out["findings"]
    )


# --- RQ-VAL-029: cobertura multipágina -------------------------------------------


def test_partial_page_coverage_blocks_completion():
    """Páginas não processadas → cobertura nunca integral, status
    honesto e declaração explícita."""
    table = _table([_row("50000001", 10, page=1)])
    bom = _bom(PRODUCT, ("50000001", PRODUCT, 1))
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001", page=1),
        drawing_pages=14,
        page_coverage={
            "pdf_page_count": 14,
            "pages_attempted": [1, 2, 3],
            "pages_ocr_ok": [1, 2, 3],
            "pages_failed": [],
            "pages_not_processed": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        },
    )
    assert out["coverage"]["complete_for_requested_scope"] is False
    assert out["coverage"]["pages_not_processed"] == [
        4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
    ]
    assert any("pages_not_processed" in l for l in out["limitations"])
    assert out["status"] == "INCONCLUSIVE"


def test_failed_page_blocks_bom_only_even_with_yield():
    """Página com OCR falho bloqueia BOM_ONLY — ausência exige
    cobertura integral de todas as páginas."""
    shared = [f"5000001{i}" for i in range(8)]
    table = _table(
        [_row(c, 10 * i, page=1) for i, c in enumerate(shared, 1)]
    )
    bom = _bom(
        PRODUCT,
        *[(c, PRODUCT, 1) for c in shared],
        ("50000019", PRODUCT, 1),
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens(*shared, page=1),
        drawing_pages=3,
        page_coverage={
            "pdf_page_count": 3,
            "pages_attempted": [1, 2],
            "pages_ocr_ok": [1],
            "pages_failed": [{"page": 2, "error": "ocr_failed"}],
            "pages_not_processed": [3],
        },
    )
    assert all(f["type"] != "BOM_ONLY" for f in out["findings"])
    assert any("pages_not_processed" in l for l in out["limitations"])


def test_tables_by_page_coverage_declared():
    """Tabelas identificadas/verificadas por página — cobertura
    auditável do escopo analisado."""
    table = _table([_row("50000001", 10, page=1), _row("50000002", 10, page=2)])
    table["tables_by_page"] = [
        {"page": 1, "candidate": True, "row_count": 1, "code_count": 1,
         "unreliable_boundary": False},
        {"page": 2, "candidate": True, "row_count": 1, "code_count": 1,
         "unreliable_boundary": True},
    ]
    bom = _bom(
        PRODUCT, ("50000001", PRODUCT, 1), ("50000002", PRODUCT, 1)
    )
    out = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        tokens=_tokens("50000001", "50000002"),
        drawing_pages=2,
    )
    assert out["coverage"]["tables_identified"] == 2
    assert out["coverage"]["tables_verified"] == 1
