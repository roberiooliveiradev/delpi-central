"""EVA VAL-01 G5 — integridade de papéis em células mescladas (Issue #131).

Cobre a classe de defeito do PDF real: a célula mesclada do bloco-pai
absorve o rótulo da coluna (``Código <produto>``) junto ao código. O
pipeline deve (a) não fragmentar essa âncora em bandas que disputam
``component_code`` de linhas de ocorrência, (b) promover a coluna a
``parent_code`` quando a prova geométrica/estrutural existe e
(c) preservar ``UNKNOWN`` quando não existe prova.

Códigos e geometria são sintéticos e generalistas — nenhum valor vem
do desenho que motivou a correção.
"""
from __future__ import annotations

from engineering_app.application.drawing.understanding import (
    apply_native_table_observations,
    drawing_structure_occurrences,
    rows_from_native_cells,
)


def _quad(x1, y1, x2, y2):
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def _cell(row, col, text, box, **extra):
    cell = {
        "row": row,
        "col": col,
        "text": text,
        "rowspan": 1,
        "colspan": 1,
        "bounding_box_px": box,
    }
    cell.update(extra)
    return cell


PARENT = "90009999"
COMPONENTS = (
    ("A", "1", "10070001", "TERMINAL ISOLADO"),
    ("B", "1", "10130002", "CABO FLEXIVEL"),
    ("C", "1", "10140003", "TERMINAL TUBULAR"),
    ("D", "3", "10350004", "CABO SILICONE"),
)


def _labeled_parent_cells(*, parent_label="Código", parent=PARENT,
                          split_anchor=False, rows=COMPONENTS):
    """Tabela DELPI com coluna-pai mesclada rotulada ``Código <pai>``.

    Layout classe-90264174: col1 = código+descrição do conjunto
    (mesclados), col4 = item+quantidade fundidos, col5 = componente,
    col6 = descrição do componente. ``split_anchor=True`` reproduz o
    payload com ``line_texts`` (rótulo e código em bandas Y distintas).
    """
    n = len(rows)
    anchor = {
        "rowspan": n + 2,
        "token_centers": [[45.0, 60.0], [75.0, 60.0]],
        "token_refs": [8, 31],
    }
    if split_anchor:
        anchor["line_texts"] = [parent_label, parent]
        anchor["line_centers"] = [40.0, 80.0]
    cells = [
        _cell(0, 1, "Código", _quad(0, 0, 110, 16)),
        _cell(0, 2, "Descrição", _quad(120, 0, 320, 16)),
        _cell(0, 4, "Item", _quad(380, 0, 440, 16)),
        _cell(0, 4, "QTD.", _quad(440, 0, 480, 16)),
        _cell(0, 5, "Comp.", _quad(490, 0, 560, 16)),
        _cell(0, 6, "Descrição", _quad(570, 0, 860, 16)),
        _cell(1, 1, f"{parent_label} {parent}", _quad(0, 20, 110, 40 + n * 30),
              **anchor),
        _cell(1, 2, "CHICOTE DO MOTOR", _quad(120, 20, 320, 40 + n * 30),
              rowspan=n + 2, token_centers=[[220.0, 110.0]]),
    ]
    for i, (item, qty, code, desc) in enumerate(rows):
        r = 1 + i
        y = 20 + i * 30
        cells.append(_cell(r, 4, f"{item} {qty}", _quad(380, y, 480, y + 20),
                           token_centers=[[420.0, y + 10.0]]))
        cells.append(_cell(r, 5, code, _quad(490, y, 560, y + 20),
                           token_centers=[[525.0, y + 10.0]]))
        cells.append(_cell(r, 6, desc, _quad(570, y, 860, y + 20),
                           token_centers=[[700.0, y + 10.0]]))
    return cells


def _understanding(rows=None, product_code=PARENT):
    return {
        "product_code": product_code,
        "document_hash_sha256": "sha:test",
        "component_table": {"rows": list(rows or [])},
    }


def _observation(cells, *, page=1, consistent=True):
    return [{
        "page": page,
        "region_type": "component_table",
        "result": {
            "cells": cells,
            "tables": [{
                "structure_consistent": consistent,
                "structure_limitations": [],
            }],
            "render": {"processed_page": page},
            "processed_pages": [page],
        },
    }]


def _by_item(rows):
    return {r["item"]: r for r in rows if r.get("item")}


# --------------------------------------------------------------------------
# TC01 — pai único mesclado rotulado + quatro componentes
# --------------------------------------------------------------------------


def test_tc01_labeled_merged_parent_yields_four_occurrences():
    cells = _labeled_parent_cells()
    rows, col_types = rows_from_native_cells(cells, page=1)
    occs = drawing_structure_occurrences(rows, product_code=PARENT)
    assert {o["component_code"] for o in occs} == {
        code for _i, _q, code, _d in COMPONENTS
    }
    assert len(occs) == len(COMPONENTS)


def test_tc01_parent_anchor_propagates_to_all_covered_rows():
    cells = _labeled_parent_cells()
    rows, _ = rows_from_native_cells(cells, page=1)
    occs = drawing_structure_occurrences(rows, product_code=PARENT)
    identified = [o for o in occs if o["parent_state"] == "IDENTIFIED"]
    assert {o["parent_code"] for o in identified} == {PARENT}
    assert len(identified) == len(COMPONENTS)


# --------------------------------------------------------------------------
# TC02 — pai e componente na mesma linha nativa não colidem
# --------------------------------------------------------------------------


def test_tc02_parent_and_component_same_native_row_no_collision():
    """A banda de código da âncora rotulada nunca disputa o campo
    ``component_code`` da linha onde a âncora está projetada."""
    cells = _labeled_parent_cells(split_anchor=True)
    rows, _ = rows_from_native_cells(cells, page=1)
    for item, _qty, code, _desc in COMPONENTS:
        row = _by_item(rows)[item]
        assert row["component_code"] == code, (item, row)
        comp_field = (row.get("fields") or {}).get("component_code") or {}
        assert comp_field.get("association_state") == "FIELD_IDENTIFIED"


# --------------------------------------------------------------------------
# TC03 — célula ``Código <code>`` (rótulo misturado) é contexto de grupo
# --------------------------------------------------------------------------


def test_tc03_header_label_mixed_code_becomes_parent_code_col():
    cells = _labeled_parent_cells()
    rows, col_types = rows_from_native_cells(cells, page=1)
    assert "parent_code" in col_types.values()
    # a célula rotulada publica papel estrutural, não componente
    parent_cells = [
        c for r in rows for c in (r.get("cells") or [])
        if c.get("col_type") == "parent_code"
    ]
    assert parent_cells


# --------------------------------------------------------------------------
# TC04 — preservação do componente cuja linha abriga a âncora
# --------------------------------------------------------------------------


def test_tc04_component_row_sharing_anchor_row_is_not_lost():
    """Equivalente estrutural à linha B: a ocorrência sobrevive mesmo
    quando a banda ``<code>`` da âncora é projetada sobre ela."""
    cells = _labeled_parent_cells(split_anchor=True)
    rows, _ = rows_from_native_cells(cells, page=1)
    occs = drawing_structure_occurrences(rows, product_code=PARENT)
    codes = {o["component_code"] for o in occs}
    assert codes == {code for _i, _q, code, _d in COMPONENTS}
    by_code = {o["component_code"]: o for o in occs}
    assert by_code["10130002"]["item"] == "B"
    assert by_code["10130002"]["quantity"] == "1"
    assert by_code["10350004"]["quantity"] == "3"


# --------------------------------------------------------------------------
# TC05 — a raiz nunca é componente de si mesma
# --------------------------------------------------------------------------


def test_tc05_root_never_emitted_as_component():
    cells = _labeled_parent_cells()
    rows, _ = rows_from_native_cells(cells, page=1)
    occs = drawing_structure_occurrences(rows, product_code=PARENT)
    assert all(o["component_code"] != PARENT for o in occs)
    for row in rows:
        assert row.get("component_code") != PARENT


# --------------------------------------------------------------------------
# TC06 — sem âncora comprovável, pai permanece UNKNOWN
# --------------------------------------------------------------------------


def _unanchored_cells():
    cells = [
        _cell(0, 0, "Item", _quad(0, 0, 60, 16)),
        _cell(0, 1, "QTD.", _quad(70, 0, 120, 16)),
        _cell(0, 2, "Código", _quad(130, 0, 260, 16)),
        _cell(0, 3, "Descrição", _quad(270, 0, 620, 16)),
    ]
    for i, (item, qty, code, desc) in enumerate(COMPONENTS):
        r = 1 + i
        y = 20 + i * 30
        cells.append(_cell(r, 0, item, _quad(0, y, 60, y + 20),
                           token_centers=[[30.0, y + 10.0]]))
        cells.append(_cell(r, 1, qty, _quad(70, y, 120, y + 20),
                           token_centers=[[95.0, y + 10.0]]))
        cells.append(_cell(r, 2, code, _quad(130, y, 260, y + 20),
                           token_centers=[[195.0, y + 10.0]]))
        cells.append(_cell(r, 3, desc, _quad(270, y, 620, y + 20),
                           token_centers=[[430.0, y + 10.0]]))
    return cells


def test_tc06_no_anchor_keeps_parent_unknown_and_components():
    rows, col_types = rows_from_native_cells(_unanchored_cells(), page=1)
    assert "parent_code" not in col_types.values()
    occs = drawing_structure_occurrences(rows, product_code=PARENT)
    assert len(occs) == len(COMPONENTS)
    assert all(o["parent_state"] == "UNKNOWN" for o in occs)
    assert all(
        "parent_not_observed" in o["uncertainty"] for o in occs
    )


# --------------------------------------------------------------------------
# TC07 — múltiplos blocos-pai rotulados, ocorrências independentes
# --------------------------------------------------------------------------


def test_tc07_repeated_component_under_distinct_labeled_parents():
    cells = [
        _cell(0, 0, "Código", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Item", _quad(90, 0, 140, 16)),
        _cell(0, 2, "Qtd", _quad(150, 0, 190, 16)),
        _cell(0, 3, "Comp.", _quad(200, 0, 300, 16)),
        _cell(0, 4, "Descrição", _quad(310, 0, 620, 16)),
    ]
    groups = (("Código 80000001", ("AE", "AH")),
              ("Código 80000002", ("AE", "AH", "AG")))
    codes = {"AE": "10010028", "AH": "10080897", "AG": "10110676"}
    r = 1
    for parent_text, items in groups:
        n = len(items)
        cells.append(_cell(r, 0, parent_text,
                           _quad(0, r * 30, 80, (r + n) * 30),
                           rowspan=n,
                           token_centers=[[40.0, r * 30 + 20.0]]))
        for k, item in enumerate(items):
            y = (r + k) * 30
            cells.append(_cell(r + k, 1, item,
                               _quad(90, y, 140, y + 20),
                               token_centers=[[115.0, y + 10.0]]))
            cells.append(_cell(r + k, 2, "1",
                               _quad(150, y, 190, y + 20),
                               token_centers=[[170.0, y + 10.0]]))
            cells.append(_cell(r + k, 3, codes[item],
                               _quad(200, y, 300, y + 20),
                               token_centers=[[250.0, y + 10.0]]))
            cells.append(_cell(r + k, 4, "DESCRICAO " + item,
                               _quad(310, y, 620, y + 20),
                               token_centers=[[430.0, y + 10.0]]))
        r += n
    rows, _ = rows_from_native_cells(cells, page=1)
    occs = drawing_structure_occurrences(rows, product_code="90000001")
    same = [o for o in occs if o["component_code"] == "10010028"]
    assert len(same) == 2
    assert {o["parent_code"] for o in same} == {"80000001", "80000002"}


# --------------------------------------------------------------------------
# TC08 — bandas fundidas/desalinhadas não transferem campos entre linhas
# --------------------------------------------------------------------------


def test_tc08_fused_item_qty_bands_do_not_contaminate_siblings():
    cells = [
        _cell(0, 0, "Item", _quad(0, 0, 40, 16)),
        _cell(0, 1, "Qtd", _quad(40, 0, 80, 16)),
        _cell(0, 2, "Codigo", _quad(90, 0, 170, 16)),
        _cell(0, 3, "Descricao", _quad(180, 0, 460, 16)),
        _cell(1, 0, "A B", _quad(0, 20, 40, 80),
              line_texts=["A", "B"], line_centers=[30.0, 60.0],
              token_centers=[[20, 30.0], [20, 60.0]]),
        _cell(1, 1, "1 1", _quad(40, 20, 80, 80),
              line_texts=["1", "1"], line_centers=[30.0, 60.0],
              token_centers=[[60, 30.0], [60, 60.0]]),
        _cell(1, 2, "10070001", _quad(90, 20, 170, 40),
              token_centers=[[130, 30.0]]),
        _cell(1, 3, "TERMINAL", _quad(180, 20, 460, 40),
              token_centers=[[300, 30.0]]),
        _cell(2, 2, "10130002", _quad(90, 50, 170, 70),
              token_centers=[[130, 60.0]]),
        _cell(2, 3, "CABO", _quad(180, 50, 460, 70),
              token_centers=[[300, 60.0]]),
        _cell(3, 0, "C", _quad(0, 80, 40, 100), token_centers=[[20, 90.0]]),
        _cell(3, 1, "2", _quad(40, 80, 80, 100), token_centers=[[60, 90.0]]),
        _cell(3, 2, "10140003", _quad(90, 80, 170, 100),
              token_centers=[[130, 90.0]]),
        _cell(3, 3, "TERMINAL C", _quad(180, 80, 460, 100),
              token_centers=[[300, 90.0]]),
        _cell(4, 0, "D", _quad(0, 110, 40, 130),
              token_centers=[[20, 120.0]]),
        _cell(4, 1, "3", _quad(40, 110, 80, 130),
              token_centers=[[60, 120.0]]),
        _cell(4, 2, "10350004", _quad(90, 110, 170, 130),
              token_centers=[[130, 120.0]]),
        _cell(4, 3, "CABO D", _quad(180, 110, 460, 130),
              token_centers=[[300, 120.0]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=1)
    by_item = _by_item(rows)
    assert by_item["A"]["component_code"] == "10070001"
    assert by_item["B"]["component_code"] == "10130002"
    assert by_item["C"]["quantity"] == "2"
    assert by_item["D"]["quantity"] == "3"


# --------------------------------------------------------------------------
# TC09 — round-trip obrigatório pela integração completa
# --------------------------------------------------------------------------


def test_tc09_full_integration_native_cells_to_occurrences():
    """native cells → rows_from_native_cells → apply_native_table_
    observations → drawing_structure_occurrences (não funções isoladas)."""
    cells = _labeled_parent_cells(split_anchor=True)
    updated = apply_native_table_observations(
        _understanding(), _observation(cells),
    )
    table = updated["component_table"]
    occs = table["structure_occurrences"]
    assert {o["component_code"] for o in occs} == {
        code for _i, _q, code, _d in COMPONENTS
    }
    assert len(occs) == len(COMPONENTS)
    assert all(o["component_code"] != PARENT for o in occs)
    identified = [o for o in occs if o["parent_state"] == "IDENTIFIED"]
    assert {o["parent_code"] for o in identified} == {PARENT}
    profiles = (table.get("presentation_profile") or {})
    assert any(
        isinstance(v, dict) and v.get("parent_code_col") is not None
        for v in profiles.values()
    )


def test_tc09_fallback_rows_preserved_when_native_rejected():
    """Sem evidência nativa utilizável, o fallback permanece (fail-closed)."""
    fallback_row = {
        "row": 0, "page": 1, "item": "A", "quantity": "1",
        "component_code": "10070001", "cells": [], "fields": {},
        "association_status": "FIELD_IDENTIFIED",
    }
    obs = [{
        "page": 1,
        "region_type": "component_table",
        "result": {
            "cells": [],
            "tables": [{
                "structure_consistent": False,
                "structure_limitations": ["rows_missing"],
            }],
            "render": {"processed_page": 1},
            "processed_pages": [1],
        },
    }]
    updated = apply_native_table_observations(
        _understanding(rows=[fallback_row]), obs,
    )
    rows = updated["component_table"]["rows"]
    assert rows and rows[0]["component_code"] == "10070001"
