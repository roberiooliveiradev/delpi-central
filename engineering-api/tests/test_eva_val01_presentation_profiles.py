"""EVA VAL-01 — perfil de apresentação DELPI e famílias de layout.

Papéis de coluna (parent_code/parent_description × item/quantity/
component_code/description) por evidência de conteúdo + posição
relativa, âncoras por papel, fonte do vínculo pai e projeção de
ocorrências. Nenhum teste assume seis colunas fixas nem coordenadas
absolutas — as famílias variam spans, ordens, densidades e paginação.
"""
from __future__ import annotations

from engineering_app.application.drawing.understanding import (
    _assign_presentation_roles,
    build_understanding,
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


def _tok(text, x, y, w=40, h=12):
    return {
        "raw_text": text,
        "normalized_text": text,
        "bounding_box_px": [x, y, x + w, y, x + w, y + h, x, y + h],
        "page": 1,
    }


def _by_item(rows):
    return {r["item"]: r for r in rows if r.get("item")}


def _occ_by_child(occs):
    out = {}
    for o in occs:
        out.setdefault((o["parent_code"], o["component_code"]), []).append(o)
    return out


# --------------------------------------------------------------------------
# Família 1 — MP direto sob produto principal (sem coluna de pai)
# --------------------------------------------------------------------------


def test_flat_table_no_parent_column_abstains_from_parent_role():
    cells = [
        _cell(0, 0, "Item", _quad(0, 0, 40, 16)),
        _cell(0, 1, "Qtd", _quad(40, 0, 80, 16)),
        _cell(0, 2, "Componente", _quad(90, 0, 170, 16)),
        _cell(0, 3, "Descricao", _quad(180, 0, 400, 16)),
        _cell(1, 0, "A1", _quad(0, 20, 40, 40), token_centers=[[20, 30]]),
        _cell(1, 1, "1", _quad(40, 20, 80, 40), token_centers=[[60, 30]]),
        _cell(1, 2, "10010028", _quad(90, 20, 170, 40), token_centers=[[130, 30]]),
        _cell(1, 3, "ANEL", _quad(180, 20, 400, 40), token_centers=[[240, 30]]),
        _cell(2, 0, "A2", _quad(0, 50, 40, 70), token_centers=[[20, 60]]),
        _cell(2, 1, "2", _quad(40, 50, 80, 70), token_centers=[[60, 60]]),
        _cell(2, 2, "10080897", _quad(90, 50, 170, 70), token_centers=[[130, 60]]),
        _cell(2, 3, "PARAFUSO", _quad(180, 50, 400, 70), token_centers=[[240, 60]]),
        _cell(3, 0, "A3", _quad(0, 80, 40, 100), token_centers=[[20, 90]]),
        _cell(3, 1, "1", _quad(40, 80, 80, 100), token_centers=[[60, 90]]),
        _cell(3, 2, "10110676", _quad(90, 80, 170, 100), token_centers=[[130, 90]]),
        _cell(3, 3, "PORCA", _quad(180, 80, 400, 100), token_centers=[[240, 90]]),
    ]
    profile = {}
    rows, col_types = rows_from_native_cells(cells, page=1, profile_out=profile)
    assert profile == {}
    assert "parent_code" not in col_types.values()
    by_item = _by_item(rows)
    assert by_item["A1"]["component_code"] == "10010028"
    assert by_item["A1"]["parent_group_candidate"] is None
    occs = drawing_structure_occurrences(rows, product_code="90264135")
    assert all(o["parent_state"] == "UNKNOWN" for o in occs)


# --------------------------------------------------------------------------
# Família 2 — vários MP sob um mesmo pai (coluna esparso × denso)
# --------------------------------------------------------------------------


def _grouped_table_cells(parent_codes=("50225702",), *, scale=1.0, x0=0, y0=0):
    """Tabela DELPI canônica: código do pai esparso à esquerda,
    item/qtd/componente/descrição densos à direita."""
    def q(a, b, c, d):
        return _quad(x0 + a * scale, y0 + b * scale,
                     x0 + c * scale, y0 + d * scale)

    def tc(x, y):
        return [[x0 + x * scale, y0 + y * scale]]

    cells = [
        _cell(0, 0, "Codigo", q(0, 0, 80, 16)),
        _cell(0, 1, "Descricao", q(80, 0, 220, 16)),
        _cell(0, 2, "Item", q(230, 0, 280, 16)),
        _cell(0, 3, "Qtd", q(280, 0, 320, 16)),
        _cell(0, 4, "Comp", q(330, 0, 420, 16)),
        _cell(0, 5, "Descricao", q(430, 0, 620, 16)),
    ]
    items = (
        ("AE", "1", "10010028", "ANEL O RING"),
        ("AH", "2", "10080897", "PARAFUSO M6"),
        ("AG", "2", "10110676", "PORCA M6"),
        ("A1", "4", "10010029", "TERMINAL"),
    )
    total_rows = 5
    r = 1
    for pi, pcode in enumerate(parent_codes):
        # pai único cobre todas as linhas de dados; multi-pai distribui
        # e o último cobre o restante (rowspan real do bloco mesclado)
        if pi == len(parent_codes) - 1:
            n = total_rows - r + 1
        else:
            n = 2
        cells.append(_cell(r, 0, pcode, q(0, r * 30, 80, (r + n) * 30),
                           rowspan=n, token_centers=tc(40, r * 30 + 20)))
        cells.append(_cell(r, 1, "SUBCONJUNTO", q(80, r * 30, 220, (r + n) * 30),
                           rowspan=n, token_centers=tc(150, r * 30 + 20)))
        for k in range(n):
            item, qty, code, desc = items[(r - 1 + k) % len(items)]
            cells.append(_cell(r + k, 2, item, q(230, (r + k) * 30, 280, (r + k) * 30 + 20),
                               token_centers=tc(255, (r + k) * 30 + 10)))
            cells.append(_cell(r + k, 3, qty, q(280, (r + k) * 30, 320, (r + k) * 30 + 20),
                               token_centers=tc(300, (r + k) * 30 + 10)))
            cells.append(_cell(r + k, 4, code, q(330, (r + k) * 30, 420, (r + k) * 30 + 20),
                               token_centers=tc(375, (r + k) * 30 + 10)))
            cells.append(_cell(r + k, 5, desc, q(430, (r + k) * 30, 620, (r + k) * 30 + 20),
                               token_centers=tc(520, (r + k) * 30 + 10)))
        r += n
    # densidade mínima para o perfil (≥4 linhas de dados)
    while r <= 5:
        item, qty, code, desc = items[(r - 1) % len(items)]
        cells.append(_cell(r, 2, item, q(230, r * 30, 280, r * 30 + 20),
                           token_centers=tc(255, r * 30 + 10)))
        cells.append(_cell(r, 3, qty, q(280, r * 30, 320, r * 30 + 20),
                           token_centers=tc(300, r * 30 + 10)))
        cells.append(_cell(r, 4, code, q(330, r * 30, 420, r * 30 + 20),
                           token_centers=tc(375, r * 30 + 10)))
        cells.append(_cell(r, 5, desc, q(430, r * 30, 620, r * 30 + 20),
                           token_centers=tc(520, r * 30 + 10)))
        r += 1
    return cells


def test_presentation_profile_assigns_parent_code_and_description():
    cells = _grouped_table_cells()
    profile = {}
    rows, col_types = rows_from_native_cells(cells, page=1, profile_out=profile)
    assert profile.get("profile_id") == "delpi_structure_table"
    assert col_types.get("0") == "parent_code" or col_types.get(0) == "parent_code"
    assert col_types.get("1") == "parent_description" or col_types.get(1) == "parent_description"
    assert {r.get("parent_group_candidate") for r in rows if r.get("item")} == {"50225702"}
    # células do bloco pai publicadas com o papel — não campos
    parent_cells = [
        c for r in rows for c in r["cells"]
        if c.get("col_type") == "parent_code"
    ]
    assert parent_cells
    assert all(r.get("component_code") != "50225702" for r in rows)


def test_occurrences_preserve_parent_path_and_level():
    cells = _grouped_table_cells()
    rows, _ = rows_from_native_cells(cells, page=1)
    occs = drawing_structure_occurrences(
        rows, product_code="90264135", document_hash="sha:x",
    )
    assert occs
    by = _occ_by_child(occs)
    hits = by.get(("50225702", "10010028"))
    assert hits and hits[0]["drawing_level"] == 1
    assert hits[0]["level_basis"] == "visual_root_candidate"
    assert hits[0]["parent_evidence"] in {
        "rowspan_anchor", "column_span", "y_anchor_nearest",
        "y_anchor_correction",
    }
    assert hits[0]["occurrence_key"]["parent_path"] == "50225702"


# --------------------------------------------------------------------------
# Família 4 — mesmo componente sob pais diferentes = duas ocorrências
# --------------------------------------------------------------------------


def test_same_component_two_parents_two_occurrences():
    cells = _grouped_table_cells(parent_codes=("50225701", "50225702"))
    rows, _ = rows_from_native_cells(cells, page=1)
    occs = drawing_structure_occurrences(rows)
    same = [o for o in occs if o["component_code"] == "10010028"]
    parents = {o["parent_code"] for o in same}
    assert len(same) >= 2
    assert "50225701" in parents or "50225702" in parents


# --------------------------------------------------------------------------
# Família 5 — pai que também é filho: cadeia visual deriva nível
# --------------------------------------------------------------------------


def test_parent_that_is_also_child_chains_level():
    rows = [
        {"row": 1, "page": 1, "item": "A", "quantity": "1",
         "component_code": "50225702",
         "parent_group_candidate": "90264135",
         "parent_group_source": "column_span",
         "fields": {}, "cells": [],
         "association_status": "FIELD_IDENTIFIED"},
        {"row": 2, "page": 1, "item": "AE", "quantity": "1",
         "component_code": "10010028",
         "parent_group_candidate": "50225702",
         "parent_group_source": "column_span",
         "fields": {}, "cells": [],
         "association_status": "FIELD_IDENTIFIED"},
    ]
    occs = drawing_structure_occurrences(rows, product_code="90264135")
    by = {o["component_code"]: o for o in occs}
    assert by["50225702"]["drawing_level"] == 1
    assert by["50225702"]["level_basis"] == "chain_to_product_code"
    assert by["10010028"]["drawing_level"] == 2
    assert by["10010028"]["level_basis"] == "chain_to_product_code"
    assert by["10010028"]["hierarchy_path"] == [
        "90264135", "50225702", "10010028",
    ]


def test_ambiguous_parent_chain_abstains_level():
    rows = [
        {"row": 1, "component_code": "50225702",
         "parent_group_candidate": "90264135", "page": 1,
         "fields": {}, "cells": [], "association_status": "FIELD_IDENTIFIED"},
        {"row": 2, "component_code": "50225702",
         "parent_group_candidate": "90264000", "page": 1,
         "fields": {}, "cells": [], "association_status": "FIELD_IDENTIFIED"},
        {"row": 3, "component_code": "10010028",
         "parent_group_candidate": "50225702", "page": 1,
         "fields": {}, "cells": [], "association_status": "FIELD_IDENTIFIED"},
    ]
    occs = drawing_structure_occurrences(rows)
    by = {o["component_code"]: o for o in occs}
    assert by["10010028"]["drawing_level"] is None
    assert "ambiguous_parent_chain" in by["10010028"]["uncertainty"]


# --------------------------------------------------------------------------
# Família 8 — descrição multilinha não vira linhas nem pai
# --------------------------------------------------------------------------


def test_multiline_description_stays_single_row():
    cells = [
        _cell(0, 0, "Item", _quad(0, 0, 40, 16)),
        _cell(0, 1, "Codigo", _quad(90, 0, 170, 16)),
        _cell(0, 2, "Descricao", _quad(180, 0, 460, 16)),
        _cell(1, 0, "A1", _quad(0, 20, 40, 60), token_centers=[[20, 40]]),
        _cell(1, 1, "10010028", _quad(90, 20, 170, 60), token_centers=[[130, 40]]),
        _cell(1, 2, "CONECTOR RECEPTACULO 2 VIAS SUPERSEAL",
              _quad(180, 20, 460, 60),
              line_texts=["CONECTOR RECEPTACULO", "2 VIAS SUPERSEAL"],
              line_centers=[30.0, 50.0],
              token_centers=[[280, 30.0], [280, 50.0]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=1)
    assert len([r for r in rows if r.get("component_code")]) == 1


# --------------------------------------------------------------------------
# Família 9 — variante com coluna Cabo
# --------------------------------------------------------------------------


def test_cable_column_variant_keeps_roles():
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Item", _quad(90, 0, 130, 16)),
        _cell(0, 2, "Qtd", _quad(140, 0, 180, 16)),
        _cell(0, 3, "Cabo", _quad(190, 0, 250, 16)),
        _cell(0, 4, "Comp", _quad(260, 0, 350, 16)),
        _cell(0, 5, "Descricao", _quad(360, 0, 560, 16)),
        _cell(1, 0, "50225701", _quad(0, 20, 80, 60), rowspan=2,
              token_centers=[[40, 40]]),
        _cell(1, 1, "AE", _quad(90, 20, 130, 40), token_centers=[[110, 30]]),
        _cell(1, 2, "1", _quad(140, 20, 180, 40), token_centers=[[160, 30]]),
        _cell(1, 3, "CB-01", _quad(190, 20, 250, 40), token_centers=[[220, 30]]),
        _cell(1, 4, "10010028", _quad(260, 20, 350, 40), token_centers=[[305, 30]]),
        _cell(1, 5, "CABO 2V", _quad(360, 20, 560, 40), token_centers=[[460, 30]]),
        _cell(2, 1, "AH", _quad(90, 50, 130, 70), token_centers=[[110, 60]]),
        _cell(2, 2, "2", _quad(140, 50, 180, 70), token_centers=[[160, 60]]),
        _cell(2, 3, "CB-02", _quad(190, 50, 250, 70), token_centers=[[220, 60]]),
        _cell(2, 4, "10080897", _quad(260, 50, 350, 70), token_centers=[[305, 60]]),
        _cell(2, 5, "CABO 4V", _quad(360, 50, 560, 70), token_centers=[[460, 60]]),
        _cell(3, 0, "50225702", _quad(0, 80, 80, 120), rowspan=2,
              token_centers=[[40, 100]]),
        _cell(3, 1, "AE", _quad(90, 80, 130, 100), token_centers=[[110, 90]]),
        _cell(3, 2, "1", _quad(140, 80, 180, 100), token_centers=[[160, 90]]),
        _cell(3, 3, "CB-03", _quad(190, 80, 250, 100), token_centers=[[220, 90]]),
        _cell(3, 4, "10010028", _quad(260, 80, 350, 100), token_centers=[[305, 90]]),
        _cell(3, 5, "CABO 2V", _quad(360, 80, 560, 100), token_centers=[[460, 90]]),
        _cell(4, 1, "AG", _quad(90, 110, 130, 130), token_centers=[[110, 120]]),
        _cell(4, 2, "2", _quad(140, 110, 180, 130), token_centers=[[160, 120]]),
        _cell(4, 3, "CB-04", _quad(190, 110, 250, 130), token_centers=[[220, 120]]),
        _cell(4, 4, "10110676", _quad(260, 110, 350, 130), token_centers=[[305, 120]]),
        _cell(4, 5, "CABO 6V", _quad(360, 110, 560, 130), token_centers=[[460, 120]]),
    ]
    profile = {}
    rows, col_types = rows_from_native_cells(cells, page=1, profile_out=profile)
    assert col_types.get("3") == "cable" or col_types.get(3) == "cable"
    by_item = _by_item(rows)
    assert by_item["AH"]["component_code"] == "10080897"
    assert by_item["AH"]["parent_group_candidate"] == "50225701"
    assert by_item["AG"]["parent_group_candidate"] == "50225702"


# --------------------------------------------------------------------------
# Família 10 — colunas reordenadas (descrição antes do código pai)
# --------------------------------------------------------------------------


def test_reordered_columns_roles_follow_content_not_position():
    cells = [
        _cell(0, 0, "Descricao", _quad(0, 0, 140, 16)),
        _cell(0, 1, "Codigo", _quad(150, 0, 230, 16)),
        _cell(0, 2, "Item", _quad(240, 0, 290, 16)),
        _cell(0, 3, "Qtd", _quad(290, 0, 330, 16)),
        _cell(0, 4, "Comp", _quad(340, 0, 430, 16)),
        _cell(1, 0, "SUBCONJUNTO A", _quad(0, 20, 140, 80), rowspan=3,
              token_centers=[[70, 50]]),
        _cell(1, 1, "50225702", _quad(150, 20, 230, 80), rowspan=3,
              token_centers=[[190, 50]]),
        _cell(1, 2, "AE", _quad(240, 20, 290, 40), token_centers=[[265, 30]]),
        _cell(1, 3, "1", _quad(290, 20, 330, 40), token_centers=[[310, 30]]),
        _cell(1, 4, "10010028", _quad(340, 20, 430, 40), token_centers=[[385, 30]]),
        _cell(2, 2, "AH", _quad(240, 45, 290, 65), token_centers=[[265, 55]]),
        _cell(2, 3, "2", _quad(290, 45, 330, 65), token_centers=[[310, 55]]),
        _cell(2, 4, "10080897", _quad(340, 45, 430, 65), token_centers=[[385, 55]]),
        _cell(3, 2, "AG", _quad(240, 70, 290, 90), token_centers=[[265, 80]]),
        _cell(3, 3, "2", _quad(290, 70, 330, 90), token_centers=[[310, 80]]),
        _cell(3, 4, "10110676", _quad(340, 70, 430, 90), token_centers=[[385, 80]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=1)
    by_item = _by_item(rows)
    assert by_item["AH"]["parent_group_candidate"] == "50225702"
    assert by_item["AH"]["component_code"] == "10080897"


# --------------------------------------------------------------------------
# Família 11 — escala/posição distinta (offset + escala diferente)
# --------------------------------------------------------------------------


def test_scaled_and_shifted_table_same_roles():
    cells = _grouped_table_cells(scale=0.5, x0=400, y0=800)
    profile = {}
    rows, col_types = rows_from_native_cells(cells, page=3, profile_out=profile)
    assert any(
        v == "parent_code" for v in col_types.values()
    )
    assert all(r.get("parent_group_candidate") == "50225702"
               for r in rows if r.get("item"))


# --------------------------------------------------------------------------
# Família 12 — quantidade sem célula SLANet correspondente
# --------------------------------------------------------------------------


def test_missing_quantity_cell_stays_none_not_invented():
    cells = [
        _cell(0, 0, "Item", _quad(0, 0, 40, 16)),
        _cell(0, 1, "Qtd", _quad(40, 0, 80, 16)),
        _cell(0, 2, "Codigo", _quad(90, 0, 170, 16)),
        _cell(1, 0, "A1", _quad(0, 20, 40, 40), token_centers=[[20, 30]]),
        _cell(1, 1, "", _quad(40, 20, 80, 40)),
        _cell(1, 2, "10010028", _quad(90, 20, 170, 40), token_centers=[[130, 30]]),
    ]
    rows, _ = rows_from_native_cells(cells, page=1)
    by_item = _by_item(rows)
    assert by_item["A1"]["component_code"] == "10010028"
    assert by_item["A1"]["quantity"] in (None, "")


# --------------------------------------------------------------------------
# Família 15 — perfil nunca atribuído por densidade equilibrada
# --------------------------------------------------------------------------


def test_balanced_code_columns_no_parent_role_assigned():
    cells = [
        _cell(0, 0, "Codigo", _quad(0, 0, 80, 16)),
        _cell(0, 1, "Item", _quad(90, 0, 130, 16)),
        _cell(0, 2, "Comp", _quad(190, 0, 280, 16)),
        _cell(1, 0, "50225701", _quad(0, 20, 80, 40), token_centers=[[40, 30]]),
        _cell(1, 1, "AE", _quad(90, 20, 130, 40), token_centers=[[110, 30]]),
        _cell(1, 2, "10010028", _quad(190, 20, 280, 40), token_centers=[[235, 30]]),
        _cell(2, 0, "50225702", _quad(0, 50, 80, 70), token_centers=[[40, 60]]),
        _cell(2, 1, "AH", _quad(90, 50, 130, 70), token_centers=[[110, 60]]),
        _cell(2, 2, "10080897", _quad(190, 50, 280, 70), token_centers=[[235, 60]]),
        _cell(3, 0, "50225703", _quad(0, 80, 80, 100), token_centers=[[40, 90]]),
        _cell(3, 1, "AG", _quad(90, 80, 130, 100), token_centers=[[110, 90]]),
        _cell(3, 2, "10110676", _quad(190, 80, 280, 100), token_centers=[[235, 90]]),
    ]
    profile = {}
    rows, col_types = rows_from_native_cells(cells, page=1, profile_out=profile)
    # duas colunas de código igualmente densas → sem prova de pai
    assert "parent_code" not in col_types.values()
