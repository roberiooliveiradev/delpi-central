"""DEC-VAL-040 — integridade de associação (banda Y e grupo × componente).

Fixtures abaixo registram a geometria observada nos jobs MCP
``aj-8f671a3ee1094d3e`` (90264017 p9) e ``aj-1d52deaaabc7446d``
(90264004). Não são regras de produto: o algoritmo só vê células,
tokens e papéis. Códigos de referência não entram na implementação.
"""
from engineering_app.application.drawing.drawing_investigation import (
    _table_candidates,
)
from engineering_app.application.drawing.understanding import (
    rows_from_native_cells,
)
from engineering_app.application.drawing.understanding_object_mapper import (
    populate_from_understanding,
)
from engineering_app.domain.drawing.object_profiles import (
    DrawingObjectSet,
    ObjectType,
)


PDF_90264017 = (
    "5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee"
)
PDF_90264004 = (
    "5b6717dfa7b8dcdc18f81b4657e1dcdf3410b9af42c8cf3109214df2f66719f4"
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


def _header():
    return [
        _cell(0, 0, "Item", _quad(0, 0, 40, 16)),
        _cell(0, 1, "Qtd", _quad(40, 0, 80, 16)),
        _cell(0, 2, "Codigo", _quad(90, 0, 170, 16)),
        _cell(0, 3, "Descricao", _quad(180, 0, 460, 16)),
    ]


def _by_item(rows):
    return {row["item"]: row for row in rows if row.get("item")}


def test_real_fixture_rejects_g9_cross_band_tuple():
    """G (Y≈200.5) não forma tupla com quantidade 9 e código em Y≈180.5.

    A célula nativa ``G 3 K 2`` está no mesmo índice SLANet que o
    código cuja caixa alta cobre as duas bandas; o centro do token do
    código permanece em 180.5. Evidência do job da página 9.
    """
    cells = _header() + [
        _cell(3, 2, "10091368", _quad(90, 150, 170, 168),
              token_centers=[[130, 160.0]]),
        _cell(3, 3, "CONECTOR STOCK", _quad(180, 150, 460, 168),
              token_centers=[[260, 160.0]]),
        _cell(
            4, 2, "10110676", _quad(90, 170, 170, 230),
            token_centers=[[130, 180.5]],
        ),
        _cell(
            4, 3, "ETIQUETA TERMORETRATIL AMARELO LISO",
            _quad(180, 172, 460, 190),
            token_centers=[[280, 180.5]],
        ),
        _cell(
            4, 0, "E 2 F 9 G 3 K 2", _quad(0, 150, 40, 230),
            line_texts=["E 2", "F 9", "G 3", "K 2"],
            line_centers=[160.0, 180.5, 200.5, 220.0],
            token_centers=[
                [12, 160.0], [28, 160.0],
                [12, 180.5], [28, 180.5],
                [12, 200.5], [28, 200.5],
                [12, 220.0], [28, 220.0],
            ],
        ),
        _cell(5, 2, "10110679", _quad(90, 192, 170, 210),
              token_centers=[[130, 200.5]]),
        _cell(5, 3, "ETIQUETA G LINHA", _quad(180, 192, 460, 210),
              token_centers=[[260, 200.5]]),
        _cell(6, 2, "10130020", _quad(90, 212, 170, 230),
              token_centers=[[130, 220.0]]),
        _cell(6, 3, "ETIQUETA K LINHA", _quad(180, 212, 460, 230),
              token_centers=[[260, 220.0]]),
    ]
    assert PDF_90264017
    rows, _ = rows_from_native_cells(cells, page=9)
    for row in rows:
        linked = (
            row.get("item"),
            row.get("quantity"),
            row.get("component_code"),
        )
        assert linked != ("G", "9", "10110676")
        fields = row.get("fields") or {}
        cys = [
            f.get("source_cy_px")
            for f in fields.values()
            if f.get("source_cy_px") is not None
        ]
        if len(cys) >= 2:
            assert max(cys) - min(cys) <= 12.0
    by_item = _by_item(rows)
    assert by_item["E"]["quantity"] == "2"
    assert by_item["E"]["component_code"] == "10091368"
    assert by_item["F"]["quantity"] == "9"
    assert by_item["F"]["component_code"] == "10110676"
    assert by_item["G"]["quantity"] == "3"
    assert by_item["G"]["component_code"] == "10110679"
    assert by_item["K"]["quantity"] == "2"
    assert by_item["K"]["component_code"] == "10130020"
    assert by_item["F"]["description"].startswith("ETIQUETA TERMORETRATIL")
    assert by_item["G"]["description"] == "ETIQUETA G LINHA"
    assert "10110676" not in (by_item["G"]["description"] or "")


def test_sibling_letter_is_not_joined_to_another_bands_quantity():
    """Irmão de G/9: item H na banda 200 não herda quantidade 4 da banda 180."""
    cells = _header() + [
        _cell(1, 1, "4", _quad(40, 170, 80, 190), token_centers=[[60, 180.0]]),
        _cell(1, 2, "10090001", _quad(90, 170, 170, 230),
              token_centers=[[130, 180.0]]),
        _cell(
            1, 0, "H 1 J 2", _quad(0, 170, 40, 230),
            line_texts=["H 1", "J 2"],
            line_centers=[200.0, 220.0],
            token_centers=[[12, 200.0], [28, 200.0], [12, 220.0], [28, 220.0]],
        ),
    ]
    rows, _ = rows_from_native_cells(cells, page=9)
    for row in rows:
        assert (row.get("item"), row.get("quantity"), row.get("component_code")) != (
            "H", "4", "10090001",
        )
    by_item = _by_item(rows)
    assert by_item["H"]["quantity"] == "1"
    assert by_item["H"].get("component_code") != "10090001"
    assert by_item["J"]["quantity"] == "2"


def test_group_description_does_not_fill_component_description():
    """CHICOTE DE LIGACAO é contexto do conjunto, não descrição de A2."""
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Descricao", _quad(80, 0, 250, 16)),
        _cell(0, 2, "Item", _quad(260, 0, 310, 16)),
        _cell(0, 3, "Qtd", _quad(310, 0, 350, 16)),
        _cell(0, 4, "Comp", _quad(360, 0, 450, 16)),
        _cell(0, 5, "Descricao", _quad(460, 0, 760, 16)),
        _cell(2, 0, "90264004", _quad(0, 40, 80, 140), rowspan=4,
              token_centers=[[40, 50]]),
        _cell(2, 1, "CHICOTE DE LIGACAO", _quad(80, 40, 250, 140), rowspan=4,
              token_centers=[[150, 55]]),
        _cell(1, 2, "A1", _quad(260, 20, 310, 38), token_centers=[[285, 29]]),
        _cell(1, 3, "1", _quad(310, 20, 350, 38), token_centers=[[330, 29]]),
        _cell(1, 5, "ETIQUETA ACETATO DE RAYON T1/U1", _quad(460, 20, 760, 38),
              token_centers=[[560, 29]]),
        _cell(2, 2, "A2", _quad(260, 40, 310, 58), token_centers=[[285, 49]]),
        _cell(2, 3, "1", _quad(310, 40, 350, 58), token_centers=[[330, 49]]),
        _cell(2, 4, "10110082", _quad(360, 40, 450, 58), token_centers=[[400, 49]]),
        _cell(2, 5, "ETIQUETA ACETATO DE RAYON T2/V1", _quad(460, 40, 760, 58),
              token_centers=[[560, 49]]),
        _cell(3, 2, "A3", _quad(260, 60, 310, 78), token_centers=[[285, 69]]),
        _cell(3, 3, "1", _quad(310, 60, 350, 78), token_centers=[[330, 69]]),
        _cell(3, 4, "10110083", _quad(360, 60, 450, 78), token_centers=[[400, 69]]),
        _cell(3, 5, "ETIQUETA ACETATO DE RAYON T3", _quad(460, 60, 760, 78),
              token_centers=[[560, 69]]),
        _cell(4, 2, "A7", _quad(260, 80, 310, 98), token_centers=[[285, 89]]),
        _cell(4, 3, "1", _quad(310, 80, 350, 98), token_centers=[[330, 89]]),
        # SLANet trocou as colunas: descrição no índice de código.
        _cell(4, 4, "ETIQUETA ACETATO DE RAYON 1TB1", _quad(360, 80, 450, 98),
              token_centers=[[400, 89]]),
        _cell(4, 5, "10110092", _quad(460, 80, 760, 98), token_centers=[[560, 89]]),
    ]
    assert PDF_90264004
    rows, _ = rows_from_native_cells(cells, page=1)
    by_item = _by_item(rows)
    a2 = by_item["A2"]
    assert a2["component_code"] == "10110082"
    assert a2["quantity"] == "1"
    assert a2["description"] == "ETIQUETA ACETATO DE RAYON T2/V1"
    assert a2["description"] != "CHICOTE DE LIGACAO"
    assert a2["parent_group_candidate"] == "90264004"
    assert a2["component_code"] != "90264004"
    group_cells = [
        c for c in a2["cells"] if "CHICOTE" in (c.get("text") or "")
    ]
    assert group_cells
    assert group_cells[0]["col"] != next(
        c["col"] for c in a2["cells"] if "T2/V1" in c["text"]
    )
    assert by_item["A1"]["description"] == "ETIQUETA ACETATO DE RAYON T1/U1"
    assert by_item["A1"].get("component_code") in (None, "")
    assert by_item["A3"]["component_code"] == "10110083"
    a7 = by_item["A7"]
    assert a7["component_code"] == "10110092"
    assert a7["description"] == "ETIQUETA ACETATO DE RAYON 1TB1"
    assert "ETIQUETA" not in (a7["component_code"] or "")


def test_item_on_wrong_slanet_index_follows_its_token_band():
    """Item cujo índice nativo é o da linha de cima, com centro Y da linha certa."""
    cells = _header() + [
        _cell(1, 0, "A4", _quad(0, 20, 40, 38), token_centers=[[20, 29]]),
        _cell(1, 1, "1", _quad(50, 20, 90, 38), token_centers=[[70, 29]]),
        _cell(1, 2, "10110087", _quad(100, 20, 180, 38), token_centers=[[140, 29]]),
        _cell(1, 3, "ETIQUETA ACETATO DE RAYON T4", _quad(190, 20, 460, 38),
              token_centers=[[280, 29]]),
        _cell(2, 1, "1", _quad(50, 40, 90, 58), token_centers=[[70, 49]]),
        _cell(2, 2, "10110088", _quad(100, 40, 180, 58), token_centers=[[140, 49]]),
        _cell(2, 3, "ETIQUETA ACETATO DE RAYON T5/V2", _quad(190, 40, 460, 58),
              token_centers=[[280, 49]]),
        _cell(1, 0, "A5", _quad(0, 40, 40, 58), token_centers=[[20, 49]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=1)
    by_item = _by_item(rows)
    assert by_item["A4"]["component_code"] == "10110087"
    assert by_item["A5"]["component_code"] == "10110088"
    assert by_item["A5"]["quantity"] == "1"
    assert "T5/V2" in by_item["A5"]["description"]
    assert by_item["A4"]["item"] != "A5"


def test_repeated_item_stays_inside_its_group():
    """A9 de um conjunto não absorve código nem quantidade do outro."""
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 90, 16)),
        _cell(0, 1, "Item", _quad(100, 0, 140, 16)),
        _cell(0, 2, "Qtd", _quad(150, 0, 190, 16)),
        _cell(0, 3, "Comp", _quad(200, 0, 290, 16)),
        _cell(1, 0, "50225478", _quad(0, 20, 90, 70), rowspan=2,
              token_centers=[[40, 30]]),
        _cell(1, 1, "A9", _quad(100, 20, 140, 40), token_centers=[[120, 30]]),
        _cell(1, 2, "2", _quad(150, 20, 190, 40), token_centers=[[170, 30]]),
        _cell(2, 1, "AA", _quad(100, 42, 140, 60), token_centers=[[120, 50]]),
        _cell(2, 2, "2", _quad(150, 42, 190, 60), token_centers=[[170, 50]]),
        _cell(2, 3, "10400035", _quad(200, 42, 290, 60), token_centers=[[240, 50]]),
        _cell(3, 0, "50225479", _quad(0, 70, 90, 120), rowspan=2,
              token_centers=[[40, 80]]),
        _cell(3, 1, "A9", _quad(100, 70, 140, 90), token_centers=[[120, 80]]),
        _cell(3, 2, "6", _quad(150, 70, 190, 90), token_centers=[[170, 80]]),
        _cell(3, 3, "10080065", _quad(200, 70, 290, 90), token_centers=[[240, 80]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=1)
    a9 = [r for r in rows if r.get("item") == "A9"]
    assert len(a9) == 2
    by_group = {r["parent_group_candidate"]: r for r in a9}
    assert by_group["50225478"]["quantity"] == "2"
    assert by_group["50225478"].get("component_code") in (None, "")
    assert by_group["50225479"]["quantity"] == "6"
    assert by_group["50225479"]["component_code"] == "10080065"
    assert by_group["50225478"]["component_code"] != "10080065"


def test_code_present_on_first_group_is_not_stolen_by_the_second():
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 90, 16)),
        _cell(0, 1, "Item", _quad(100, 0, 140, 16)),
        _cell(0, 2, "Qtd", _quad(150, 0, 190, 16)),
        _cell(0, 3, "Comp", _quad(200, 0, 290, 16)),
        _cell(1, 0, "50225478", _quad(0, 20, 90, 60), rowspan=2,
              token_centers=[[40, 30]]),
        _cell(1, 1, "A9", _quad(100, 20, 140, 40), token_centers=[[120, 30]]),
        _cell(1, 2, "2", _quad(150, 20, 190, 40), token_centers=[[170, 30]]),
        _cell(1, 3, "10080065", _quad(200, 20, 290, 40), token_centers=[[240, 30]]),
        _cell(2, 0, "50225479", _quad(0, 50, 90, 90), rowspan=2,
              token_centers=[[40, 60]]),
        _cell(2, 1, "A9", _quad(100, 50, 140, 70), token_centers=[[120, 60]]),
        _cell(2, 2, "6", _quad(150, 50, 190, 70), token_centers=[[170, 60]]),
        _cell(2, 3, "10080065", _quad(200, 50, 290, 70), token_centers=[[240, 60]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=1)
    a9 = [r for r in rows if r.get("item") == "A9"]
    assert {(r["parent_group_candidate"], r["quantity"], r["component_code"])
            for r in a9} == {
        ("50225478", "2", "10080065"),
        ("50225479", "6", "10080065"),
    }


def test_multiline_description_is_not_split_into_items():
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 120, 18)),
        _cell(1, 0, "10081389", _quad(0, 20, 120, 38)),
        _cell(
            2, 0, "TUBO FLEX ALTA PRESS", _quad(0, 40, 120, 70),
            line_texts=["TUBO FLEX", "ALTA PRESS"],
            line_centers=[50.0, 58.0],
        ),
        _cell(3, 0, "10081685", _quad(0, 72, 120, 90)),
    ]
    rows, _ = rows_from_native_cells(cells, page=9)
    assert len(rows) == 3
    text = " ".join(c["text"] for r in rows for c in r["cells"])
    assert "TUBO FLEX" in text and "ALTA PRESS" in text
    assert all(r.get("item") is None for r in rows)


def test_rowspan_does_not_duplicate_component_onto_next_row():
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Conjunto", _quad(90, 0, 180, 16)),
        _cell(1, 0, "10081389", _quad(0, 20, 80, 40)),
        _cell(1, 1, "70260008", _quad(90, 20, 180, 70), rowspan=2),
        _cell(2, 0, "10081685", _quad(0, 42, 80, 60)),
    ]
    rows, _ = rows_from_native_cells(cells, page=9)
    by_code = {r["component_code"]: r for r in rows}
    assert "70260008" not in by_code
    assert by_code["10081685"].get("component_code") == "10081685"
    assert all(
        c["text"] != "70260008" for c in by_code["10081685"]["cells"]
    )


def test_conflicting_tuple_is_not_an_exact_candidate():
    cells = _header() + [
        _cell(1, 1, "9", _quad(40, 170, 80, 190), token_centers=[[60, 180.5]]),
        _cell(1, 2, "10110676", _quad(90, 170, 170, 230),
              token_centers=[[130, 180.5]]),
        _cell(1, 3, "ETIQUETA TERMORETRATIL AMARELO LISO",
              _quad(180, 172, 460, 190), token_centers=[[280, 180.5]]),
        _cell(
            1, 0, "G 3 K 2", _quad(0, 170, 40, 230),
            line_texts=["G 3", "K 2"],
            line_centers=[200.5, 220.0],
            token_centers=[[12, 200.5], [28, 200.5], [12, 220.0], [28, 220.0]],
        ),
    ]
    rows, _ = rows_from_native_cells(cells, page=9)
    promoted = [
        r for r in rows
        if r.get("item") == "G"
        and r.get("quantity") == "9"
        and r.get("component_code") == "10110676"
        and r.get("association_status") == "FIELD_IDENTIFIED"
    ]
    assert promoted == []
    understanding = {"component_table": {"rows": rows}}
    candidates = _table_candidates(understanding)
    exact = [
        c for c in candidates
        if c["code"] == "10110676" and not c["ambiguous"]
        and (c["row"].get("item") == "G")
    ]
    assert exact == []
    g_rows = [r for r in rows if r.get("item") == "G"]
    assert g_rows
    assert g_rows[0].get("component_code") != "10110676"
    oset = DrawingObjectSet(document_sha=PDF_90264017)
    populate_from_understanding(
        oset, understanding, document_sha=PDF_90264017,
    )
    for obj in oset.by_type(ObjectType.DRAWING_TABLE_ITEM):
        attrs = obj.attributes
        if attrs.get("component_code_candidate") == "10110676":
            assert attrs.get("item_label") != "G"
