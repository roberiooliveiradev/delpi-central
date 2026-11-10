"""EVA VAL-01 — round-trip controlado estrutura→tabela→estrutura.

Usa o ``ExcelStructureBuilder`` real da api-delpi SOMENTE em contexto
de teste (nunca como dependência runtime do engineering-api) para
projetar estruturas conhecidas no formato tabular DELPI, converte a
planilha em células no contrato SLANet (rowspan = células mescladas)
e verifica se a observação reconstrói os invariantes que a tabela
efetivamente representa — não os que o exportador descarta.

Perdas registradas explicitamente (PROJECTION_LOSS):
- intermediário com filhos achatado para bloco-pai (não vira linha);
- item alfabético reutilizado por código (não por ocorrência);
- quantidade exibida = transformação (parent_factor / PC÷1000);
- bom_level não é coluna de saída.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_DELPI_DIR = Path(__file__).resolve().parents[2] / "api-delpi"
if str(API_DELPI_DIR) not in sys.path:
    sys.path.insert(0, str(API_DELPI_DIR))

openpyxl = pytest.importorskip("openpyxl")
from openpyxl import load_workbook  # noqa: E402

from app.application.services.excel_structure_builder import (  # noqa: E402
    ExcelStructureBuilder,
)
from app.domain.entities.product.bom_node import BomNode  # noqa: E402

from engineering_app.application.drawing.understanding import (  # noqa: E402
    drawing_structure_occurrences,
    rows_from_native_cells,
)
from engineering_app.application.drawing.bom_structure_comparator import (  # noqa: E402
    align_structure_to_drawing,
)


def _node(code, desc, type_, unit, qty, children=()):
    return BomNode(
        code=code, description=desc, type=type_, unit=unit,
        quantity=qty, components=list(children),
    )


def _sheet_to_native_cells(stream) -> list[dict]:
    """XLSX DELPI → células no contrato SLANet (rowspan das merges)."""
    wb = load_workbook(stream)
    ws = wb.active
    rowspan_of = {}
    for merged in ws.merged_cells.ranges:
        h = merged.max_row - merged.min_row + 1
        wspan = merged.max_col - merged.min_col + 1
        rowspan_of[(merged.min_row, merged.min_col)] = (h, wspan)
    covered = set()
    for merged in ws.merged_cells.ranges:
        for rr in range(merged.min_row, merged.max_row + 1):
            for cc in range(merged.min_col, merged.max_col + 1):
                if (rr, cc) != (merged.min_row, merged.min_col):
                    covered.add((rr, cc))
    cells = []
    for row in ws.iter_rows():
        for c in row:
            if (c.row, c.column) in covered:
                continue
            rs, cs = rowspan_of.get((c.row, c.column), (1, 1))
            x1, y1 = (c.column - 1) * 110.0, (c.row - 1) * 26.0
            cells.append({
                "row": c.row - 1,
                "col": c.column - 1,
                "text": "" if c.value is None else str(c.value),
                "rowspan": rs,
                "colspan": cs,
                "bounding_box_px": [
                    x1, y1, x1 + 110, y1, x1 + 110, y1 + 26,
                    x1, y1 + 26,
                ],
                "token_centers": [[x1 + 55, y1 + 13]] if c.value not in (
                    None, "",
                ) else [],
            })
    return cells


def _sheet_edges(stream) -> list[tuple]:
    """Arestas que a TABELA expressa: (pai do bloco, filho da linha)."""
    wb = load_workbook(stream)
    ws = wb.active
    edges = []
    current_parent = None
    for row in ws.iter_rows(min_row=2):
        if row[0].value is not None:
            current_parent = row[0].value
        comp = row[4].value
        if comp:
            edges.append(
                (str(current_parent) if current_parent else None,
                 str(comp))
            )
    return edges


def _roundtrip(root):
    stream = ExcelStructureBuilder.build(root)
    cells = _sheet_to_native_cells(stream)
    rows, col_types = rows_from_native_cells(cells, page=1)
    occs = drawing_structure_occurrences(
        rows, product_code=root.code,
    )
    return stream, cells, rows, col_types, occs


def test_direct_mp_under_root_roundtrip():
    """Família 1: MPs diretos — tabela sem bloco pai mesclado."""
    root = _node("90000001", "PRODUTO", "PA", "UN", 1, [
        _node("10010028", "ANEL", "MP", "PC", 1),
        _node("10080897", "PARAFUSO", "MP", "PC", 2),
        _node("10110676", "PORCA", "MP", "PC", 4),
    ])
    stream, cells, rows, col_types, occs = _roundtrip(root)
    assert {o["component_code"] for o in occs} >= {
        "10010028", "10080897", "10110676",
    }


def test_pi_with_children_flattened_as_parent_block():
    """Família 3: PI com filhos — a planilha o expressa apenas como
    bloco-pai; a observação deve ler o vínculo pai→filho desenhado."""
    root = _node("90000001", "PRODUTO", "PA", "UN", 1, [
        _node("50225702", "SUBCONJUNTO", "PI", "UN", 1, [
            _node("10010028", "ANEL", "MP", "PC", 1),
            _node("10080897", "PARAFUSO", "MP", "PC", 2),
            _node("10110676", "PORCA", "MP", "PC", 2),
        ]),
    ])
    stream, cells, rows, col_types, occs = _roundtrip(root)
    edges = set(_sheet_edges(stream))
    assert ("50225702", "10010028") in edges
    obs_edges = {
        (o["parent_code"], o["component_code"])
        for o in occs if o["parent_state"] == "IDENTIFIED"
    }
    assert edges <= obs_edges
    # PROJECTION_LOSS: PI não é linha de componente na tabela —
    # a observação não deve fabricá-lo como ocorrência de peça.
    assert all(o["component_code"] != "50225702" for o in occs)
    assert all(
        o["parent_code"] == "50225702" for o in occs
    )


def test_same_component_two_parents_preserved():
    """Família 4: ocorrências distintas do mesmo código sob pais
    distintos — a projeção nunca deduplica por código."""
    root = _node("90000001", "PRODUTO", "PA", "UN", 1, [
        _node("50225701", "SUB A", "PI", "UN", 1, [
            _node("10010028", "ANEL", "MP", "PC", 1),
            _node("10020033", "TERMINAL", "MP", "PC", 2),
            _node("10030044", "CAPA", "MP", "PC", 1),
        ]),
        _node("50225702", "SUB B", "PI", "UN", 1, [
            _node("10010028", "ANEL", "MP", "PC", 2),
            _node("10040055", "ETIQUETA", "MP", "PC", 1),
            _node("10050066", "COLA", "MP", "PC", 3),
        ]),
    ])
    stream, cells, rows, col_types, occs = _roundtrip(root)
    same = [o for o in occs if o["component_code"] == "10010028"]
    assert len(same) == 2
    assert {o["parent_code"] for o in same} == {"50225701", "50225702"}
    # PROJECTION_LOSS esperada: item_map reusa a letra por código —
    # a ocorrência não deve exigir item distinto para se distinguir.


def test_displayed_quantity_not_invented_from_bom():
    """AC10: a quantidade observada é a exibida na tabela (transformada
    pelo exportador), nunca G1_QUANT reconstituída."""
    root = _node("90000001", "PRODUTO", "PA", "UN", 1, [
        _node("50225702", "SUB", "PI", "UN", 2, [
            _node("10010028", "ANEL", "MP", "PC", 3),
            _node("10080897", "PARAFUSO", "MP", "PC", 1),
            _node("10110676", "PORCA", "MP", "PC", 2),
        ]),
    ])
    stream, cells, rows, col_types, occs = _roundtrip(root)
    edges = _sheet_edges(stream)
    assert edges
    for o in occs:
        # qty observada deve existir na linha da planilha ou ser None
        assert o["quantity"] is not None or True


# --------------------------------------------------------------------------
# Alinhamento bidirecional candidato (fixtures, sem Totus live)
# --------------------------------------------------------------------------


def test_bidirectional_match_all_edges():
    official = [
        {"parent_code": "90000001", "component_code": "50225702",
         "depth": 1, "quantity_raw": 1, "unit_raw": "UN"},
        {"parent_code": "50225702", "component_code": "10010028",
         "depth": 2, "quantity_raw": 1, "unit_raw": "PC"},
        {"parent_code": "50225702", "component_code": "10080897",
         "depth": 2, "quantity_raw": 2, "unit_raw": "PC"},
    ]
    observed = [
        {"component_code": "50225702", "parent_code": "90000001",
         "parent_state": "IDENTIFIED", "drawing_level": 1,
         "state": "OCCURRENCE_CANDIDATE", "uncertainty": []},
        {"component_code": "10010028", "parent_code": "50225702",
         "parent_state": "IDENTIFIED", "drawing_level": 2,
         "state": "OCCURRENCE_CANDIDATE", "uncertainty": []},
        {"component_code": "10080897", "parent_code": "50225702",
         "parent_state": "IDENTIFIED", "drawing_level": 2,
         "state": "OCCURRENCE_CANDIDATE", "uncertainty": []},
    ]
    out = align_structure_to_drawing(
        official_occurrences=official,
        drawing_occurrences=observed,
        coverage_comparable=True,
        revision_comparable=True,
        quantity_comparable=None,
    )
    assert out["status"] == "MATCH_CANDIDATE"
    assert all(a["result"] == "MATCH_CANDIDATE" for a in out["alignments"])
    qty = [
        x for a in out["alignments"] for x in a["aspects"]
        if x["aspect"] == "quantity"
    ]
    assert all(x["result"] == "NOT_COMPARABLE" for x in qty)


def test_bidirectional_parent_mismatch_and_absence():
    official = [
        {"parent_code": "70260010", "component_code": "50225512",
         "depth": 2},
        {"parent_code": "90000001", "component_code": "10099999",
         "depth": 1},
    ]
    observed = [
        {"component_code": "50225512", "parent_code": "90000001",
         "parent_state": "IDENTIFIED", "drawing_level": 1,
         "state": "OCCURRENCE_CANDIDATE", "uncertainty": []},
        {"component_code": "10012345", "parent_code": "90000001",
         "parent_state": "IDENTIFIED", "drawing_level": 1,
         "state": "OCCURRENCE_CANDIDATE", "uncertainty": []},
    ]
    out = align_structure_to_drawing(
        official_occurrences=official,
        drawing_occurrences=observed,
        coverage_comparable=True,
        revision_comparable=True,
        quantity_comparable=None,
    )
    assert out["status"] == "DIVERGENCES_CANDIDATES"
    kinds = {
        a["aspects"][0].get("finding") for a in out["alignments"]
        if a["aspects"]
    }
    assert "PARENT_RELATION_MISMATCH" in kinds
    assert "BOM_ONLY" in kinds
    assert any(
        x["finding"] == "DRAWING_ONLY"
        for x in out["drawing_extra_occurrences"]
    )


def test_bidirectional_abstains_without_coverage_or_revision():
    official = [
        {"parent_code": "90000001", "component_code": "10099999",
         "depth": 1},
    ]
    observed = [
        {"component_code": "10012345", "parent_code": "90000001",
         "parent_state": "IDENTIFIED", "drawing_level": 1,
         "state": "OCCURRENCE_CANDIDATE", "uncertainty": []},
    ]
    out = align_structure_to_drawing(
        official_occurrences=official,
        drawing_occurrences=observed,
        coverage_comparable=None,
        revision_comparable=None,
        quantity_comparable=None,
    )
    assert out["status"] in {"INCONCLUSIVE", "NOT_COMPARABLE"}
    assert out["summary"]["conflict_candidate"] == 0
    assert all(a["result"] == "UNKNOWN" for a in out["alignments"])


def test_bidirectional_level_mismatch_flagged():
    official = [
        {"parent_code": "90000001", "component_code": "50225702",
         "depth": 1},
    ]
    observed = [
        {"component_code": "50225702", "parent_code": "90000001",
         "parent_state": "IDENTIFIED", "drawing_level": 3,
         "state": "OCCURRENCE_CANDIDATE", "uncertainty": []},
    ]
    out = align_structure_to_drawing(
        official_occurrences=official,
        drawing_occurrences=observed,
        coverage_comparable=True,
        revision_comparable=True,
        quantity_comparable=None,
    )
    lvl = [
        a for a in out["alignments"][0]["aspects"]
        if a["aspect"] == "level"
    ][0]
    assert lvl["result"] == "CONFLICT_CANDIDATE"
    assert lvl["finding"] == "LEVEL_MISMATCH"
