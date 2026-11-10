"""EVA VAL-01 G4 — integração mínima de tabelas (crop, line_texts, papéis).

Fixtures reproduzem classes de defeito G2/G3 (fusão de códigos,
rodapé administrativo, subset≠componente). Códigos e geometria são
evidência de caso; a implementação não pode calibrar-se a um PDF.
"""
from __future__ import annotations

from engineering_app.application.drawing.understanding import (
    build_understanding,
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


def _tok(text, x, y, w=40, h=12):
    return {
        "raw_text": text,
        "normalized_text": text,
        "bounding_box_px": [x, y, x + w, y, x + w, y + h, x, y + h],
        "page": 1,
    }


def _header_item_qty_code_desc():
    return [
        _cell(0, 0, "Item", _quad(0, 0, 40, 16)),
        _cell(0, 1, "Qtd", _quad(40, 0, 80, 16)),
        _cell(0, 2, "Codigo", _quad(90, 0, 170, 16)),
        _cell(0, 3, "Descricao", _quad(180, 0, 460, 16)),
    ]


def _by_item(rows):
    return {row["item"]: row for row in rows if row.get("item")}


def _component_region(result):
    for region in result["regions"]:
        if region["type"] == "component_table":
            return region
    return None


# ----- G4-B positivos -----


def test_g4_fused_component_codes_split_by_line_texts_geometry():
    """Duas bandas OCR de códigos distintos → duas ocorrências (classe A2/A3)."""
    cells = _header_item_qty_code_desc() + [
        _cell(1, 0, "A2", _quad(0, 100, 40, 130), token_centers=[[20, 117.0]]),
        _cell(1, 1, "1", _quad(40, 100, 80, 130), token_centers=[[60, 117.0]]),
        _cell(
            1, 2, "10080192 10090316", _quad(90, 100, 170, 160),
            line_texts=["10080192", "10090316"],
            line_centers=[117.0, 147.5],
            token_centers=[[130, 117.0], [130, 147.5]],
        ),
        _cell(
            1, 3, "SUPORTE SUPERIOR", _quad(180, 100, 460, 130),
            token_centers=[[280, 117.0]],
        ),
        _cell(2, 0, "A3", _quad(0, 140, 40, 160), token_centers=[[20, 147.5]]),
        _cell(2, 1, "2", _quad(40, 140, 80, 160), token_centers=[[60, 147.5]]),
        _cell(
            2, 3, "SUPORTE INFERIOR", _quad(180, 140, 460, 160),
            token_centers=[[280, 147.5]],
        ),
    ]
    rows, _ = rows_from_native_cells(cells, page=10)
    by_item = _by_item(rows)
    assert by_item["A2"]["component_code"] == "10080192"
    assert by_item["A2"]["quantity"] == "1"
    assert "SUPORTE SUPERIOR" in (by_item["A2"]["description"] or "")
    assert by_item["A3"]["component_code"] == "10090316"
    assert by_item["A3"]["quantity"] == "2"
    assert "SUPORTE INFERIOR" in (by_item["A3"]["description"] or "")
    fused = [
        r for r in rows
        if (r.get("component_code") or "") == "10080192 10090316"
    ]
    assert fused == []


def test_g4_fused_codes_alone_still_split_without_sibling_spans():
    """Sem faixas Y de colunas irmãs, bandas de código geometricamente
    distintas ainda geram ocorrências separadas."""
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 100, 16)),
        _cell(
            1, 0, "10080192 10090316", _quad(0, 20, 100, 70),
            line_texts=["10080192", "10090316"],
            line_centers=[30.0, 60.0],
            token_centers=[[50, 30.0], [50, 60.0]],
        ),
    ]
    rows, _ = rows_from_native_cells(cells, page=10)
    codes = sorted(
        r.get("component_code") for r in rows if r.get("component_code")
    )
    assert codes == ["10080192", "10090316"]


# ----- G4-C positivos -----


def test_g4_sparse_pure_code_column_acts_as_group_without_rowspan():
    """SLANet perdeu rowspan: códigos puros esparsos à esquerda ainda
    ancoram filhos até o próximo código puro da coluna."""
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Item", _quad(90, 0, 130, 16)),
        _cell(0, 2, "Qtd", _quad(140, 0, 180, 16)),
        _cell(0, 3, "Comp", _quad(190, 0, 280, 16)),
        # coluna esparsa de subconjunto (rowspan=1 em cada âncora)
        _cell(1, 0, "50225701", _quad(0, 20, 80, 40),
              token_centers=[[40, 30]]),
        _cell(1, 1, "AE", _quad(90, 20, 130, 40), token_centers=[[110, 30]]),
        _cell(1, 2, "1", _quad(140, 20, 180, 40), token_centers=[[160, 30]]),
        _cell(1, 3, "10010028", _quad(190, 20, 280, 40),
              token_centers=[[235, 30]]),
        _cell(2, 1, "AH", _quad(90, 50, 130, 70), token_centers=[[110, 60]]),
        _cell(2, 2, "2", _quad(140, 50, 180, 70), token_centers=[[160, 60]]),
        _cell(2, 3, "10080897", _quad(190, 50, 280, 70),
              token_centers=[[235, 60]]),
        _cell(3, 0, "50225702", _quad(0, 80, 80, 100),
              token_centers=[[40, 90]]),
        _cell(3, 1, "AE", _quad(90, 80, 130, 100), token_centers=[[110, 90]]),
        _cell(3, 2, "1", _quad(140, 80, 180, 100), token_centers=[[160, 90]]),
        _cell(3, 3, "10010028", _quad(190, 80, 280, 100),
              token_centers=[[235, 90]]),
        _cell(4, 1, "AH", _quad(90, 110, 130, 130), token_centers=[[110, 120]]),
        _cell(4, 2, "2", _quad(140, 110, 180, 130), token_centers=[[160, 120]]),
        _cell(4, 3, "10080897", _quad(190, 110, 280, 130),
              token_centers=[[235, 120]]),
        _cell(5, 1, "AG", _quad(90, 140, 130, 160), token_centers=[[110, 150]]),
        _cell(5, 2, "2", _quad(140, 140, 180, 160), token_centers=[[160, 150]]),
        _cell(5, 3, "10110676", _quad(190, 140, 280, 160),
              token_centers=[[235, 150]]),
        # coluna densa de componentes (acima) — já preenchida; sem 2ª
        # coluna densa extra: densidade de itens ancora a esparsa.
    ]
    rows, _ = rows_from_native_cells(cells, page=12)
    assert all(r.get("component_code") != "50225702" for r in rows)
    by_item = _by_item(rows)
    assert by_item["AE"]["parent_group_candidate"] in {
        "50225701", "50225702",
    }
    # filhos do segundo grupo
    second = [
        r for r in rows
        if r.get("parent_group_candidate") == "50225702"
    ]
    assert {r.get("item") for r in second} >= {"AE", "AH", "AG"}
    assert {r.get("component_code") for r in second} >= {
        "10010028", "10080897", "10110676",
    }


def test_g4_subset_parent_links_children_when_rowspan_present():
    """Subconjunto com rowspan → parent_group; AE/AH/AG preservados."""
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Descricao", _quad(80, 0, 220, 16)),
        _cell(0, 2, "Item", _quad(230, 0, 280, 16)),
        _cell(0, 3, "Qtd", _quad(280, 0, 320, 16)),
        _cell(0, 4, "Comp", _quad(330, 0, 420, 16)),
        _cell(0, 5, "Descricao", _quad(430, 0, 620, 16)),
        _cell(
            1, 0, "50225702", _quad(0, 20, 80, 120), rowspan=3,
            token_centers=[[40, 40]],
        ),
        _cell(
            1, 1, "SUBCONJUNTO VALVULA", _quad(80, 20, 220, 120), rowspan=3,
            token_centers=[[150, 45]],
        ),
        _cell(1, 2, "AE", _quad(230, 20, 280, 40), token_centers=[[255, 30]]),
        _cell(1, 3, "1", _quad(280, 20, 320, 40), token_centers=[[300, 30]]),
        _cell(1, 4, "10010028", _quad(330, 20, 420, 40),
              token_centers=[[375, 30]]),
        _cell(1, 5, "ANEL O RING", _quad(430, 20, 620, 40),
              token_centers=[[520, 30]]),
        _cell(2, 2, "AH", _quad(230, 50, 280, 70), token_centers=[[255, 60]]),
        _cell(2, 3, "2", _quad(280, 50, 320, 70), token_centers=[[300, 60]]),
        _cell(2, 4, "10080897", _quad(330, 50, 420, 70),
              token_centers=[[375, 60]]),
        _cell(2, 5, "PARAFUSO M6", _quad(430, 50, 620, 70),
              token_centers=[[520, 60]]),
        _cell(3, 2, "AG", _quad(230, 80, 280, 100), token_centers=[[255, 90]]),
        _cell(3, 3, "2", _quad(280, 80, 320, 100), token_centers=[[300, 90]]),
        _cell(3, 4, "10110676", _quad(330, 80, 420, 100),
              token_centers=[[375, 90]]),
        _cell(3, 5, "PORCA M6", _quad(430, 80, 620, 100),
              token_centers=[[520, 90]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=12)
    by_item = _by_item(rows)
    assert set(by_item) >= {"AE", "AH", "AG"}
    assert by_item["AE"]["component_code"] == "10010028"
    assert by_item["AH"]["component_code"] == "10080897"
    assert by_item["AG"]["component_code"] == "10110676"
    assert by_item["AE"]["parent_group_candidate"] == "50225702"
    assert by_item["AH"]["parent_group_candidate"] == "50225702"
    assert by_item["AG"]["parent_group_candidate"] == "50225702"
    # subset não vira ocorrência de componente
    assert all(r.get("component_code") != "50225702" for r in rows)


def test_g4_missing_parent_in_crop_does_not_invent_link():
    """Filhos presentes sem âncora de grupo → ocorrências sem pai inventado."""
    cells = _header_item_qty_code_desc() + [
        _cell(1, 0, "AE", _quad(0, 20, 40, 40), token_centers=[[20, 30]]),
        _cell(1, 1, "1", _quad(40, 20, 80, 40), token_centers=[[60, 30]]),
        _cell(1, 2, "10010028", _quad(90, 20, 170, 40),
              token_centers=[[130, 30]]),
        _cell(1, 3, "ANEL", _quad(180, 20, 300, 40), token_centers=[[240, 30]]),
        _cell(2, 0, "AH", _quad(0, 50, 40, 70), token_centers=[[20, 60]]),
        _cell(2, 1, "2", _quad(40, 50, 80, 70), token_centers=[[60, 60]]),
        _cell(2, 2, "10080897", _quad(90, 50, 170, 70),
              token_centers=[[130, 60]]),
        _cell(2, 3, "PARAFUSO", _quad(180, 50, 300, 70),
              token_centers=[[240, 60]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=12)
    by_item = _by_item(rows)
    assert by_item["AE"]["component_code"] == "10010028"
    assert by_item["AH"]["component_code"] == "10080897"
    assert by_item["AE"].get("parent_group_candidate") in (None, "")
    assert by_item["AH"].get("parent_group_candidate") in (None, "")


def test_g4_repeated_component_under_different_parents_not_deduped():
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Item", _quad(90, 0, 130, 16)),
        _cell(0, 2, "Qtd", _quad(140, 0, 180, 16)),
        _cell(0, 3, "Comp", _quad(190, 0, 280, 16)),
        _cell(1, 0, "50225701", _quad(0, 20, 80, 60), rowspan=2,
              token_centers=[[40, 30]]),
        _cell(1, 1, "A1", _quad(90, 20, 130, 40), token_centers=[[110, 30]]),
        _cell(1, 2, "1", _quad(140, 20, 180, 40), token_centers=[[160, 30]]),
        _cell(1, 3, "10010028", _quad(190, 20, 280, 40),
              token_centers=[[235, 30]]),
        _cell(3, 0, "50225702", _quad(0, 70, 80, 110), rowspan=2,
              token_centers=[[40, 80]]),
        _cell(3, 1, "AE", _quad(90, 70, 130, 90), token_centers=[[110, 80]]),
        _cell(3, 2, "1", _quad(140, 70, 180, 90), token_centers=[[160, 80]]),
        _cell(3, 3, "10010028", _quad(190, 70, 280, 90),
              token_centers=[[235, 80]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=12)
    same = [r for r in rows if r.get("component_code") == "10010028"]
    assert len(same) == 2
    parents = {r.get("parent_group_candidate") for r in same}
    assert parents == {"50225701", "50225702"}


# ----- G4-P12 structural boundary (crop + hierarchy) -----


def test_g4_dual_code_columns_crop_keeps_parent_and_component_band():
    """Duas colunas de código (conjunto esparso + componente denso) com
    itens entre elas: o crop preserva ambas e não engole ruído à direita.

    Classe da first-loss P12 — envelope page-wide degrada o SLANet.
    """
    tokens = []
    # coluna esquerda (pai/subconjunto) — esparsa
    for index, code in enumerate(("50225701", "50225702", "50225703")):
        y = 300 + index * 90
        tokens.append(_tok(code, 200, y, 70))
    # itens + qty entre colunas
    for index, (item, qty) in enumerate(
        (("AE", "1"), ("AH", "2"), ("AG", "2"), ("AE", "1"), ("AH", "2"), ("AG", "2"),
         ("AE", "1"), ("AH", "2"), ("AG", "2"))
    ):
        y = 300 + index * 30
        tokens.extend((_tok(item, 780, y, 24), _tok(qty, 860, y, 16)))
    # coluna direita (componentes) — densa
    for index, code in enumerate(
        ("10010028", "10080897", "10110676") * 3
    ):
        y = 300 + index * 30
        tokens.append(_tok(code, 980, y, 70))
        tokens.append(_tok("DESC", 1100, y, 80))
    # ruído de carimbo / margem direita (não pode puxar o crop)
    tokens.extend((
        _tok("90264135", 2000, 100, 70),
        _tok("CLIENTE", 2050, 140, 60),
        _tok("REV", 2050, 180, 40),
        _tok("01", 2120, 180, 24),
    ))
    result = build_understanding(
        tokens, document_hash="x", page=12, render_size_px=(2339, 1653),
    )
    region = _component_region(result)
    assert region is not None
    box = region["box_px"]
    assert box[0] <= 200, box
    assert box[2] >= 1050, box
    # não page-wide: ruído em x≈2000 fora do núcleo
    assert box[2] < 1800, box
    assert (box[2] - box[0]) * (box[3] - box[1]) <= 2339 * 1653 * 0.55


def test_g4_centered_group_label_assigns_children_above_and_below():
    """Rótulo de conjunto centrado na célula mesclada: filhos acima e
    abaixo do token do pai herdam o mesmo parent_group_candidate."""
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Item", _quad(90, 0, 130, 16)),
        _cell(0, 2, "Qtd", _quad(140, 0, 180, 16)),
        _cell(0, 3, "Comp", _quad(190, 0, 280, 16)),
        _cell(1, 0, "50225701", _quad(0, 20, 80, 80), rowspan=3,
              token_centers=[[40, 50]]),
        _cell(1, 1, "AE", _quad(90, 20, 130, 40), token_centers=[[110, 30]]),
        _cell(1, 2, "1", _quad(140, 20, 180, 40), token_centers=[[160, 30]]),
        _cell(1, 3, "10010011", _quad(190, 20, 280, 40),
              token_centers=[[235, 30]]),
        _cell(2, 1, "AH", _quad(90, 50, 130, 70), token_centers=[[110, 60]]),
        _cell(2, 2, "2", _quad(140, 50, 180, 70), token_centers=[[160, 60]]),
        _cell(2, 3, "10010012", _quad(190, 50, 280, 70),
              token_centers=[[235, 60]]),
        # pai seguinte: token Y no meio; filho AE acima do token
        _cell(3, 0, "50225702", _quad(0, 80, 80, 160), rowspan=3,
              token_centers=[[40, 120]]),
        _cell(3, 1, "AE", _quad(90, 85, 130, 105), token_centers=[[110, 95]]),
        _cell(3, 2, "1", _quad(140, 85, 180, 105), token_centers=[[160, 95]]),
        _cell(3, 3, "10010028", _quad(190, 85, 280, 105),
              token_centers=[[235, 95]]),
        _cell(4, 1, "AH", _quad(90, 115, 130, 135), token_centers=[[110, 125]]),
        _cell(4, 2, "2", _quad(140, 115, 180, 135), token_centers=[[160, 125]]),
        _cell(4, 3, "10080897", _quad(190, 115, 280, 135),
              token_centers=[[235, 125]]),
        _cell(5, 1, "AG", _quad(90, 145, 130, 165), token_centers=[[110, 155]]),
        _cell(5, 2, "2", _quad(140, 145, 180, 165), token_centers=[[160, 155]]),
        _cell(5, 3, "10110676", _quad(190, 145, 280, 165),
              token_centers=[[235, 155]]),
        _cell(6, 0, "50225703", _quad(0, 170, 80, 230), rowspan=2,
              token_centers=[[40, 200]]),
        _cell(6, 1, "AE", _quad(90, 175, 130, 195), token_centers=[[110, 185]]),
        _cell(6, 2, "1", _quad(140, 175, 180, 195), token_centers=[[160, 185]]),
        _cell(6, 3, "10010028", _quad(190, 175, 280, 195),
              token_centers=[[235, 185]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=12)
    kids = [
        r for r in rows
        if r.get("parent_group_candidate") == "50225702"
    ]
    assert {r.get("item") for r in kids} >= {"AE", "AH", "AG"}
    by_code = {r.get("component_code"): r for r in kids}
    assert by_code["10010028"]["item"] == "AE"
    assert by_code["10010028"]["quantity"] == "1"
    assert by_code["10080897"]["item"] == "AH"
    assert by_code["10080897"]["quantity"] == "2"
    assert by_code["10110676"]["item"] == "AG"
    assert by_code["10110676"]["quantity"] == "2"
    # AE do próximo pai não fica sob 50225702
    ae_next = [
        r for r in rows
        if r.get("item") == "AE" and r.get("component_code") == "10010028"
        and r.get("parent_group_candidate") == "50225703"
    ]
    assert ae_next


def test_g4_fused_quantity_line_texts_split_like_items():
    """Quantidades fundidas ('2 2') com bandas Y distintas → duas qtds."""
    cells = _header_item_qty_code_desc() + [
        _cell(
            1, 0, "AH AG", _quad(0, 20, 40, 70),
            line_texts=["AH", "AG"],
            line_centers=[30.0, 60.0],
            token_centers=[[20, 30.0], [20, 60.0]],
        ),
        _cell(
            1, 1, "2 2", _quad(40, 20, 80, 70),
            line_texts=["2", "2"],
            line_centers=[30.0, 60.0],
            token_centers=[[60, 30.0], [60, 60.0]],
        ),
        _cell(1, 2, "10080897", _quad(90, 20, 170, 40),
              token_centers=[[130, 30.0]]),
        _cell(1, 3, "TERM", _quad(180, 20, 300, 40),
              token_centers=[[240, 30.0]]),
        _cell(2, 2, "10110676", _quad(90, 50, 170, 70),
              token_centers=[[130, 60.0]]),
        _cell(2, 3, "ETIQ", _quad(180, 50, 300, 70),
              token_centers=[[240, 60.0]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=12)
    by_item = _by_item(rows)
    assert by_item["AH"]["component_code"] == "10080897"
    assert by_item["AH"]["quantity"] == "2"
    assert by_item["AG"]["component_code"] == "10110676"
    assert by_item["AG"]["quantity"] == "2"


# ----- G4-A positivos -----


def test_g4_sheet_index_strip_excluded_from_table_crop():
    """Faixa horizontal de índices 1..N próxima à última linha tabular
    (classe G2 p13) não entra no crop nem vira célula de componente."""
    tokens = []
    for index, (item, qty, code) in enumerate(
        (("A1", "1", "11111111"), ("A2", "1", "22222222"), ("A3", "2", "33333333"))
    ):
        y = 480 + index * 28
        tokens.extend((
            _tok(item, 100, y, 24),
            _tok(qty, 160, y, 16),
            _tok(code, 220, y, 70),
            _tok("CABO", 340, y, 60),
        ))
    # índices de quadro logo abaixo da última linha (vão demonstrável)
    footer_y = 580
    for i in range(1, 9):
        tokens.append(_tok(str(i), 80 + i * 120, footer_y, 18, 14))
    result = build_understanding(
        tokens, document_hash="x", page=1, render_size_px=(1200, 700),
    )
    region = _component_region(result)
    assert region is not None
    # margem de célula (~altura mediana) não pode engolir a faixa de índices
    assert region["box_px"][3] < footer_y - 4
    rows = (result.get("component_table") or {}).get("rows") or []
    assert all(
        (r.get("component_code") or "") not in {"4", "5", "4 5", "1 2 3 4 5"}
        for r in rows
    )
    texts = [
        c.get("text") for r in rows for c in (r.get("cells") or [])
    ]
    assert "4" not in texts and "5" not in texts


def test_g4_page_index_cell_not_promoted_as_component_code():
    """Célula '4 5' tipada na coluna de código não vira component_code."""
    cells = _header_item_qty_code_desc() + [
        _cell(1, 0, "A1", _quad(0, 20, 40, 40), token_centers=[[20, 30]]),
        _cell(1, 1, "1", _quad(40, 20, 80, 40), token_centers=[[60, 30]]),
        _cell(1, 2, "11111111", _quad(90, 20, 170, 40),
              token_centers=[[130, 30]]),
        _cell(1, 3, "CABO", _quad(180, 20, 300, 40), token_centers=[[240, 30]]),
        _cell(2, 2, "4 5", _quad(90, 50, 170, 70), token_centers=[[130, 60]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=13)
    assert all(r.get("component_code") != "4 5" for r in rows)
    assert all(r.get("component_code") != "4" for r in rows)
    assert all(r.get("component_code") != "5" for r in rows)
    by_item = _by_item(rows)
    assert by_item["A1"]["component_code"] == "11111111"


# ----- Negativos -----


def test_g4_multiline_description_not_split_into_components():
    cells = _header_item_qty_code_desc() + [
        _cell(1, 0, "A1", _quad(0, 20, 40, 40), token_centers=[[20, 30]]),
        _cell(1, 1, "1", _quad(40, 20, 80, 40), token_centers=[[60, 30]]),
        _cell(1, 2, "10081389", _quad(90, 20, 170, 40),
              token_centers=[[130, 30]]),
        _cell(
            1, 3, "TUBO FLEX ALTA PRESS", _quad(180, 20, 400, 60),
            line_texts=["TUBO FLEX", "ALTA PRESS"],
            line_centers=[28.0, 48.0],
            token_centers=[[280, 28.0], [280, 48.0]],
        ),
    ]
    rows, _ = rows_from_native_cells(cells, page=9)
    assert len([r for r in rows if r.get("component_code")]) == 1
    assert rows[0]["description"] and "TUBO FLEX" in rows[0]["description"]


def test_g4_legitimate_rowspan_not_split():
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Comp", _quad(90, 0, 180, 16)),
        _cell(1, 0, "50225478", _quad(0, 20, 80, 70), rowspan=2,
              token_centers=[[40, 30]]),
        _cell(1, 1, "10080065", _quad(90, 20, 180, 40),
              token_centers=[[135, 30]]),
        _cell(2, 1, "10080066", _quad(90, 45, 180, 65),
              token_centers=[[135, 55]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=9)
    assert all(r.get("component_code") != "50225478" for r in rows)
    codes = {r.get("component_code") for r in rows}
    assert "10080065" in codes and "10080066" in codes


def test_g4_code_cited_in_description_is_not_extra_occurrence():
    cells = _header_item_qty_code_desc() + [
        _cell(1, 0, "A3", _quad(0, 20, 40, 40), token_centers=[[20, 30]]),
        _cell(1, 1, "1", _quad(40, 20, 80, 40), token_centers=[[60, 30]]),
        _cell(1, 2, "10090316", _quad(90, 20, 170, 40),
              token_centers=[[130, 30]]),
        _cell(
            1, 3, "CONECTOR REF 10090317", _quad(180, 20, 400, 40),
            token_centers=[[280, 30]],
        ),
    ]
    rows, _ = rows_from_native_cells(cells, page=10)
    codes = [r.get("component_code") for r in rows if r.get("component_code")]
    assert codes == ["10090316"]
    assert "10090317" not in codes


def test_g4_dual_codes_without_geometry_are_not_blindly_split():
    """Dois códigos no mesmo texto sem line_centers distintos → abstenção."""
    cells = _header_item_qty_code_desc() + [
        _cell(1, 0, "A2", _quad(0, 20, 40, 40), token_centers=[[20, 30]]),
        _cell(1, 1, "1", _quad(40, 20, 80, 40), token_centers=[[60, 30]]),
        _cell(
            1, 2, "10080192 10090316", _quad(90, 20, 170, 40),
            token_centers=[[130, 30]],
        ),
        _cell(1, 3, "KIT", _quad(180, 20, 300, 40), token_centers=[[240, 30]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=10)
    # Sem geometria de bandas, não inventar duas ocorrências.
    codes = [r.get("component_code") for r in rows if r.get("component_code")]
    assert "10080192" not in codes or "10090316" not in codes or len(codes) == 1
    assert not (
        "10080192" in codes
        and "10090316" in codes
        and len([c for c in codes if c in ("10080192", "10090316")]) == 2
        and all(
            r.get("component_code") in ("10080192", "10090316") for r in rows
            if r.get("component_code")
        )
        and len(rows) >= 2
        and all(r.get("item") == "A2" for r in rows if r.get("component_code"))
    )


def test_g4_near_edge_legitimate_code_row_not_trimmed():
    """Última linha de códigos próxima à borda permanece no crop."""
    tokens = []
    for index, code in enumerate(("11111111", "22222222", "33333333")):
        y = 480 + index * 24
        tokens.extend((
            _tok(f"A{index+1}", 100, y, 24),
            _tok("1", 160, y, 16),
            _tok(code, 220, y, 70),
        ))
    result = build_understanding(
        tokens, document_hash="x", page=1, render_size_px=(800, 600),
    )
    region = _component_region(result)
    assert region is not None
    assert region["box_px"][3] >= 520
    rows = (result.get("component_table") or {}).get("rows") or []
    codes = {r.get("component_code") for r in rows}
    assert "33333333" in codes or any(
        "33333333" in (c.get("text") or "")
        for r in rows for c in (r.get("cells") or [])
    )
