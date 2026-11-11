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


# ---------- generalização G5-RCA: classes de falha 128/138/061 ----------


def _prefixed_anchor_cells():
    """Classe 90264061: letra de zona fundida ao código (token atômico).

    'A 90001111' rowspan=4 cobre 3 linhas de componentes; '80002222'
    rowspan=2 cobre a última. Sem prefixo reconhecido → 0 pais.
    """
    cells = [
        _cell(0, 0, "A 90001111", _quad(0, 20, 90, 140), rowspan=4,
              token_centers=[[45.0, 80.0]]),
        _cell(0, 1, "CHICOTE", _quad(100, 20, 300, 140), rowspan=4),
        _cell(4, 0, "80002222", _quad(0, 140, 90, 180), rowspan=2),
        _cell(4, 1, "CABO PRETO", _quad(100, 140, 300, 180), rowspan=2),
    ]
    rows = [("A1", "10090001"), ("A2", "10090002"), ("A3", "10090003"),
            ("A5", "10090005")]
    ys = [40, 70, 100, 160]
    for i, (item, code) in enumerate(rows):
        r = i if i < 3 else 4
        y = ys[i]
        cells += [
            _cell(r, 2, item, _quad(310, y, 360, y + 20)),
            _cell(r, 3, "1", _quad(370, y, 400, y + 20)),
            _cell(r, 4, code, _quad(410, y, 480, y + 20)),
        ]
    return cells


def test_prefixed_group_anchor_with_rowspan_recovers_parent():
    rows, _ = rows_from_native_cells(_prefixed_anchor_cells(), page=1)
    by_item = {r.get("item"): r for r in rows}
    # A linha do marcador 'A' perde o item quando o OCR a funde ao
    # código (comportamento real do PDF 061); o pai é preservado.
    assert by_item["A2"]["parent_group_candidate"] == "90001111"
    assert by_item["A3"]["parent_group_candidate"] == "90001111"
    assert by_item["A5"]["parent_group_candidate"] == "80002222"
    assert rows[0].get("parent_group_candidate") == "90001111"


def test_prefixed_code_without_rowspan_is_not_anchor():
    cells = _prefixed_anchor_cells()
    cells[0]["rowspan"] = 1
    # Sem segunda âncora e sem rowspan a coluna não é promovida:
    # prefixo isolado não é evidência estrutural de bloco-pai.
    cells = [c for c in cells if c["text"] != "80002222"]
    rows, _ = rows_from_native_cells(cells, page=1)
    assert rows and all(
        r.get("parent_group_candidate") != "90001111" for r in rows
    )


def _dense_parent_col_cells():
    """Classe 90264138: cada conjunto abre bloco curto na coluna-pai.

    c1 = códigos de conjunto densos (6 pais em 14 linhas), c3 = item,
    c4 = QTD+componente fundidos. Promoção por posição sob item_band,
    não por esparsidade — e bloco de 1 linha é âncora legítima.
    """
    cells = [
        _cell(0, 1, "Código 80010001", _quad(60, 0, 200, 20),
              line_texts=["Código", "80010001"],
              line_centers=[8.0, 12.0]),
        _cell(0, 2, "Descrição", _quad(210, 0, 380, 20)),
        _cell(0, 3, "Item", _quad(390, 0, 440, 20)),
        _cell(0, 4, "QTD. Componente", _quad(450, 0, 560, 20)),
    ]
    parents = ["80010002", "80010003", "80010004", "80010005"]
    comps = [["1 10070001"], ["1 10070002"], ["1 10070003"],
             ["1 10070004"]]
    items = [["C"], ["A"], ["B"], ["A"]]
    r = 1
    for pi, parent in enumerate(parents):
        cells.append(
            _cell(r, 1, parent, _quad(60, 20 + r * 20, 200, 40 + r * 20))
        )
        cells.append(_cell(r, 2, f"CB18PRET-{pi}",
                           _quad(210, 20 + r * 20, 380, 40 + r * 20)))
        for bi, (item, qc) in enumerate(zip(items[pi], comps[pi])):
            rr = r + bi
            code = qc.split()[-1]
            cells.append(_cell(rr, 3, item,
                               _quad(390, 20 + rr * 20, 440, 40 + rr * 20)))
            cells.append(_cell(rr, 4, qc,
                               _quad(450, 20 + rr * 20, 520, 40 + rr * 20)))
            cells.append(_cell(rr, 5, code,
                               _quad(530, 20 + rr * 20, 600, 40 + rr * 20)))
        r += len(items[pi])
    return cells


def test_dense_parent_column_promoted_under_item_band():
    rows, col_types = rows_from_native_cells(
        _dense_parent_col_cells(), page=1
    )
    assert col_types.get("1") == "parent_code"
    occ = drawing_structure_occurrences(rows, product_code="80010000")
    parents = {o["parent_code"] for o in occ if o.get("item")}
    assert parents == {"80010002", "80010003", "80010004", "80010005"}
    assert all(o["parent_state"] == "IDENTIFIED" for o in occ)
    # Códigos de conjunto nunca emitem como componente.
    assert not {o["component_code"] for o in occ} & {
        "80010002", "80010003", "80010004", "80010005"
    }


def test_mixed_column_is_not_promoted_to_parent():
    """Coluna com componentes avulsos + conjuntos não vira parent_code.

    Classe DEC040: códigos de linha sem componente em outra coluna são
    componentes, não pais — o veto preserva a emissão de componente.
    """
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 100, 16)),
        _cell(0, 2, "Item", _quad(200, 0, 250, 16)),
    ]
    for i in range(1, 4):
        y = i * 20
        cells += [
            _cell(i, 0, f"1011008{i}", _quad(0, y, 100, y + 16)),
            _cell(i, 1, f"ETIQUETA A{i}", _quad(110, y, 190, y + 16)),
            _cell(i, 2, f"A{i}", _quad(200, y, 250, y + 16)),
            _cell(i, 3, "1", _quad(260, y, 290, y + 16)),
        ]
    rows, col_types = rows_from_native_cells(cells, page=1)
    assert col_types.get("0") != "parent_code"
    by_item = {r.get("item"): r for r in rows}
    assert by_item["A1"]["component_code"] == "10110081"


def test_grid_extent_fill_repairs_empty_cell_and_anchors_block():
    """Classe 90264128: célula rowspan vazia com bbox truncada.

    Token órfão dentro da extensão linhas×colunas da grade é associado
    com proveniência; fora da extensão permanece unassigned.
    """
    from engineering_app.application.drawing.perception_contract import (
        fill_empty_cells_from_unassigned_grid_extent as fill,
    )

    cells = [
        _cell(0, 0, "PAI", _quad(10, 0, 100, 30)),
        _cell(1, 0, "", _quad(10, 30, 100, 60), rowspan=3),
        _cell(1, 1, "A1", _quad(110, 30, 160, 50)),
        _cell(2, 1, "A2", _quad(110, 50, 160, 70)),
        _cell(3, 1, "A3", _quad(110, 70, 160, 90)),
    ]
    tokens = [
        {"text": "80005005", "bounding_box_px": _quad(30, 62, 90, 78)},
        {"text": "LIXO", "bounding_box_px": _quad(300, 300, 320, 320)},
    ]
    remaining = fill(cells, tokens, [0, 1])
    assert remaining == [1]
    assert cells[1]["text"] == "80005005"
    assert cells[1]["association_method"] == "grid_extent_unassigned"
    assert cells[1]["ambiguous"] is True


def test_rehomed_band_crossing_parent_boundary_stays_unknown():
    """Banda que migra para linha de outro bloco-pai: pai ≠ IDENTIFIED."""
    cells = [
        _cell(0, 0, "80020001", _quad(0, 0, 90, 40), rowspan=2,
              token_centers=[[40.0, 20.0]]),
        _cell(2, 0, "80020002", _quad(0, 40, 90, 80), rowspan=2,
              token_centers=[[40.0, 60.0]]),
        _cell(0, 1, "A", _quad(100, 0, 140, 20)),
        _cell(0, 2, "1 10080001", _quad(150, 0, 260, 20)),
        # banda do componente migrada para a linha do bloco seguinte
        _cell(1, 1, "B", _quad(100, 20, 140, 40)),
        _cell(2, 2, "1 10080002", _quad(150, 40, 260, 60),
              _rehomed_from_row=0, _split_done=True,
              _split_text="1 10080002"),
        _cell(3, 1, "C", _quad(100, 60, 140, 80)),
        _cell(3, 2, "1 10080003", _quad(150, 60, 260, 80)),
    ]
    rows, _ = rows_from_native_cells(cells, page=1)
    occ = drawing_structure_occurrences(rows, product_code="80020000")
    migrated = [
        o for o in occ if o["component_code"] == "10080002"
    ]
    assert migrated and all(
        o["parent_state"] == "UNKNOWN" for o in migrated
    )


def test_grid_extent_disambiguates_by_column_role():
    """Classe 061-A6: token órfão coberto por duas células vazias.

    A célula do código existe mas seu bbox não contém o token; a célula
    vizinha (descrição) também está vazia. O papel da coluna — provado
    pelo conteúdo das irmãs — decide; sem coluna compatível única o
    token permanece unassigned.
    """
    from engineering_app.application.drawing.perception_contract import (
        fill_empty_cells_from_unassigned_grid_extent as fill,
    )

    cells = [
        _cell(0, 0, "A5", _quad(300, 30, 360, 50)),
        _cell(0, 1, "2", _quad(370, 30, 400, 50)),
        # código largo estende a banda da coluna de código sobre a
        # coluna vizinha — reproduz a sobreposição real do 061
        _cell(0, 2, "10080010", _quad(410, 30, 560, 50)),
        _cell(0, 3, "TERMINAL ISOLADO", _quad(490, 30, 700, 50)),
        _cell(1, 0, "A6", _quad(300, 50, 360, 70)),
        _cell(1, 1, "2", _quad(370, 50, 400, 70)),
        _cell(1, 2, "", _quad(370, 52, 480, 74)),
        _cell(1, 3, "", _quad(490, 52, 700, 74)),
    ]
    token = {
        "text": "10211552",
        # centro dentro das extensões de AMBAS as células vazias,
        # fora do bbox declarado de qualquer uma
        "bounding_box_px": _quad(478, 56, 548, 60),
    }
    remaining = fill(cells, [token], [0])
    assert remaining == []
    assert cells[6]["text"] == "10211552"
    assert cells[6]["association_method"] == "grid_extent_unassigned"
    assert cells[7]["text"] == ""


def test_grid_extent_competition_without_role_stays_unassigned():
    """Sem prova de papel (colunas com perfil idêntico) → fail-closed."""
    from engineering_app.application.drawing.perception_contract import (
        fill_empty_cells_from_unassigned_grid_extent as fill,
    )

    cells = [
        _cell(0, 0, "10080010", _quad(410, 30, 560, 50)),
        _cell(0, 1, "10380035", _quad(460, 30, 560, 50)),
        _cell(1, 0, "", _quad(410, 52, 480, 74)),
        _cell(1, 1, "", _quad(490, 52, 560, 74)),
    ]
    token = {
        "text": "10211552",
        # coberto pelas extensões das duas células vazias; ambas as
        # colunas são de código → empate → fail-closed
        "bounding_box_px": _quad(478, 56, 548, 60),
    }
    remaining = fill(cells, [token], [0])
    assert remaining == [0]
    assert all(c["text"] == "" for c in cells[2:])


# ---------- G6-closure: costura entre recuperação visual e recovery BOM ----------


def test_bom_guided_recovery_skips_code_present_in_tokens():
    """Dedup de camadas: código já observado nos tokens não dispara
    reinspeção — a BOM guia a hipótese, nunca o resultado."""
    from engineering_app.application.drawing.drawing_investigation import (
        apply_localized_recovery,
    )

    u = {
        "component_table": {
            "rows": [
                {"page": 1, "cells": [{"text": "10080010"}]},
            ],
        },
        "document_hash_sha256": "x" * 64,
    }
    tokens = [{"normalized_text": "10211552", "raw_text": "10211552",
               "page": 1, "bounding_box_px": [0, 0, 5, 0, 5, 5, 0, 5]}]
    class _NoopRenderer:
        def render_region(self, *a, **k):  # pragma: no cover
            raise AssertionError("crop indiscriminado não permitido")
    recovered = apply_localized_recovery(
        u, product_code="90009999",
        bom_component_codes=["10211552"],
        opts={"renderer": _NoopRenderer(), "ocr": None,
              "pdf_bytes": b"%PDF"},
        tokens=tokens,
    )
    assert recovered == []


def test_bom_guided_recovery_never_fabricates_absent_code():
    """Código oficial ausente de células E tokens → hipótese de
    reinspeção, mas sem evidência visual o resultado é vazio."""
    from engineering_app.application.drawing.drawing_investigation import (
        apply_localized_recovery,
    )

    class _NoopOcr:
        def extract_text(self, _img):
            class _R:
                tokens = []
            return _R()

    class _Renderer:
        def render_region(self, *a, **k):
            class _R:
                image_bytes = b"png"
                offset_px = (0.0, 0.0)
                width = height = 10
                page = 1
                dpi = 150
            return _R()

    u = {
        "component_table": {
            "rows": [
                {"page": 1,
                 "cells": [{"text": "10080010",
                            "bounding_box_px": [0, 0, 5, 0, 5, 5, 0, 5]}]},
            ],
        },
        "document_hash_sha256": "x" * 64,
    }
    recovered = apply_localized_recovery(
        u, product_code="90009999",
        bom_component_codes=["99999999"],
        opts={"renderer": _Renderer(), "ocr": _NoopOcr(),
              "pdf_bytes": b"%PDF",
              "budget": {"max_crops": 1, "max_dpi": 200,
                         "max_pixels": 4_000_000},
              "reference_dpi": 150},
        tokens=[],
    )
    assert recovered == []
    assert not u.get("localized_recovery")


def test_recovered_cell_counts_as_visual_evidence_for_dedup():
    """Célula reparada pelo fill (token órfão → célula vazia) alimenta
    o conjunto visível — a camada BOM não re-processa o que já foi
    provado visualmente."""
    from engineering_app.application.drawing.perception_contract import (
        fill_empty_cells_from_unassigned_grid_extent as fill,
    )
    from engineering_app.application.drawing.drawing_investigation import (
        apply_localized_recovery,
    )

    cells = [
        _cell(0, 0, "A1", _quad(10, 10, 40, 30)),
        _cell(0, 1, "1", _quad(50, 10, 70, 30)),
        _cell(0, 2, "10080010", _quad(80, 10, 140, 30)),
        _cell(1, 0, "A2", _quad(10, 30, 40, 50)),
        _cell(1, 1, "1", _quad(50, 30, 70, 50)),
        _cell(1, 2, "", _quad(80, 30, 140, 50)),
    ]
    tokens = [{"raw_text": "10211552", "page": 1,
               "bounding_box_px": _quad(80, 32, 140, 46)}]
    remaining = fill(cells, tokens, [0])
    assert remaining == [] and cells[5]["text"] == "10211552"
    u = {
        "component_table": {
            "rows": [
                {"page": 1, "cells": [{"text": c["text"]} for c in cells]},
            ],
        },
    }
    recovered = apply_localized_recovery(
        u, product_code="90009999",
        bom_component_codes=["10211552"],
        opts={"renderer": None, "ocr": None, "pdf_bytes": b"%PDF"},
        tokens=tokens,
    )
    assert recovered == []


# ---------- RQ-A02: recuperação do campo item (marcador em papel incorreto) ----


def test_item_marker_in_wrong_role_cell_recovered():
    """Célula 'A5' tipada parent_description na banda da linha → item."""
    from engineering_app.application.drawing.understanding import (
        _recover_item_markers,
    )

    qty = {"normalized_value": "2", "bounding_box_px": _quad(50, 10, 70, 30),
           "source_cy_px": 20.0}
    rows = [{"page": 1, "fields": {"quantity": qty, "component_code": {
        "normalized_value": "10081799",
        "bounding_box_px": _quad(80, 10, 140, 30), "source_cy_px": 20.0}},
        "cells": [
            _cell(0, 0, "50225531", _quad(0, 0, 40, 60)),
            _cell(0, 2, "A5", _quad(42, 10, 50, 30)),
        ], "parent_group_candidate": "50225531"}]
    _recover_item_markers(rows, band_gap_px=12.0)
    assert rows[0]["item"] == "A5"


def test_item_marker_outside_row_band_not_recovered():
    """Marcador de outra linha (deslocamento de grade) não migra."""
    from engineering_app.application.drawing.understanding import (
        _recover_item_markers,
    )

    qty = {"normalized_value": "6", "bounding_box_px": _quad(50, 100, 70, 120),
           "source_cy_px": 110.0}
    rows = [{"page": 1, "fields": {"quantity": qty, "component_code": {
        "normalized_value": "10400035",
        "bounding_box_px": _quad(80, 100, 140, 120), "source_cy_px": 110.0}},
        "cells": [], "parent_group_candidate": "50225479"},
        {"page": 1, "fields": {},
         "cells": [_cell(1, 0, "AA", _quad(30, 60, 50, 80))]}]
    _recover_item_markers(rows, band_gap_px=12.0)
    assert rows[0].get("item") is None


def test_item_marker_anchor_like_cell_not_recovered():
    """'A 90264061' contém código longo — nunca vira marcador."""
    from engineering_app.application.drawing.understanding import (
        _recover_item_markers,
    )

    qty = {"normalized_value": "1", "bounding_box_px": _quad(50, 10, 70, 30),
           "source_cy_px": 20.0}
    rows = [{"page": 1, "fields": {"quantity": qty, "component_code": {
        "normalized_value": "10091505",
        "bounding_box_px": _quad(80, 10, 140, 30), "source_cy_px": 20.0}},
        "cells": [_cell(0, 0, "A 90264061", _quad(0, 0, 40, 60))],
        "parent_group_candidate": "90264061"}]
    _recover_item_markers(rows, band_gap_px=12.0)
    assert rows[0].get("item") is None


def test_item_marker_two_candidates_fail_closed():
    """Dois marcadores distintos na banda → nenhum promovido."""
    from engineering_app.application.drawing.understanding import (
        _recover_item_markers,
    )

    qty = {"normalized_value": "1", "bounding_box_px": _quad(50, 10, 70, 30),
           "source_cy_px": 20.0}
    rows = [{"page": 1, "fields": {"quantity": qty, "component_code": {
        "normalized_value": "10091505",
        "bounding_box_px": _quad(80, 10, 140, 30), "source_cy_px": 20.0}},
        "cells": [_cell(0, 2, "A1", _quad(30, 10, 45, 30)),
                  _cell(0, 2, "A5", _quad(31, 10, 46, 30))],
        "parent_group_candidate": "90264061"}]
    _recover_item_markers(rows, band_gap_px=12.0)
    assert rows[0].get("item") is None
