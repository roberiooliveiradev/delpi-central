"""EVA VAL-01 — recuperação de âncoras de conjunto fundidas (Issue #131).

Classe de defeito: a SLANet emite UMA célula-âncora (rowspan>1)
contendo DOIS códigos de conjunto em bandas Y distintas (ex.:
``"<code1> B <code2>"``). O split de bandas projeta o segundo
código como fragmento ``_from_group_anchor``, mas ele nunca
reancora — a linha da banda seguinte herda o grupo anterior e o
código real do conjunto some da estrutura.

Segunda classe: código de conjunto real no PDF visto pelo OCR mas
sem célula SLANet (token órfão na faixa-X da coluna-pai) — só pode
ancorar linhas ainda sem âncora estrutural.

Códigos e geometria são sintéticos e generalistas.
"""
from __future__ import annotations

from engineering_app.application.drawing.understanding import (
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


def _comp(row, item, qty, code, cy):
    """Linha componente: item, quantidade, código, descrição."""
    return [
        _cell(row, 3, item, _quad(370, cy - 8, 430, cy + 8)),
        _cell(row, 4, qty, _quad(440, cy - 8, 480, cy + 8)),
        _cell(row, 5, code, _quad(490, cy - 8, 560, cy + 8)),
        _cell(row, 6, "DESCRICAO DO COMPONENTE", _quad(570, cy - 8, 860, cy + 8)),
    ]


def _header():
    return [
        _cell(0, 1, "Código", _quad(20, 0, 200, 14)),
        _cell(0, 2, "Descrição", _quad(210, 0, 360, 14)),
        _cell(0, 3, "Item", _quad(370, 0, 430, 14)),
        _cell(0, 4, "QTD.", _quad(440, 0, 480, 14)),
        _cell(0, 5, "Comp.", _quad(490, 0, 560, 14)),
        _cell(0, 6, "Descrição", _quad(570, 0, 860, 14)),
    ]


def _anchors(rows):
    return {
        (r["parent_group_candidate"], r["parent_group_source"])
        for r in rows
    }


def _row_group(rows, row):
    for r in rows:
        if r["row"] == row:
            return r["parent_group_candidate"], r["parent_group_source"]
    return None, None


def _fused_cells(*, fragment_letter=None):
    """Tabela com célula-âncora fundida contendo dois conjuntos.

    Conjunto ``50000010``: linhas 1-2 (rowspan declarado).
    Linha 3: componente sem âncora (UNKNOWN esperado).
    Célula fundida na linha 4: ``50000020 [B] 50000030`` com duas
    bandas — conjunto 50000020 cobre linhas 4-6, conjunto 50000030
    cobre linhas 7-8 (a banda do segundo código projeta o
    fragmento na linha 7).
    Conjunto ``50000040``: linha 9 (âncora de linha única).
    """
    frag_text = (
        f"{fragment_letter} 50000030" if fragment_letter else "50000030"
    )
    fused = _cell(
        4, 0, "50000020" + (f" {fragment_letter}" if fragment_letter else "")
        + " 50000030",
        _quad(14, 100, 92, 260),
        rowspan=5,
        token_refs=[71, 85, 86],
        token_centers=[[80.0, 122.0], [80.0, 212.0], [24.0, 215.0]],
        line_texts=["50000020", frag_text],
        line_centers=[122.0, 212.0],
        ambiguous=True,
    )
    cells = list(_header())
    cells += [
        _cell(1, 1, "50000010", _quad(60, 20, 200, 90), rowspan=2,
              token_centers=[[120.0, 55.0]]),
        _cell(1, 2, "CONJUNTO A", _quad(210, 20, 360, 90), rowspan=2),
    ]
    cells += _comp(1, "A1", "1", "10000001", 40)
    cells += _comp(2, "A2", "1", "10000002", 70)
    cells += _comp(3, "A3", "1", "10000003", 105)
    cells.append(fused)
    cells += _comp(4, "A4", "1", "10000004", 120)
    cells += _comp(5, "A5", "1", "10000005", 150)
    cells += _comp(6, "A6", "1", "10000006", 180)
    cells += _comp(7, "A7", "1", "10000007", 210)
    cells += _comp(8, "A8", "1", "10000008", 240)
    cells += [
        _cell(9, 1, "50000040", _quad(60, 262, 200, 296), rowspan=2),
        _cell(9, 2, "CONJUNTO D", _quad(210, 262, 360, 296), rowspan=2),
    ]
    cells += _comp(9, "A9", "1", "10000009", 270)
    cells += _comp(10, "A10", "1", "10000010", 300)
    return cells


def test_fused_anchor_second_group_code_recovered_leading_code():
    rows, _ = rows_from_native_cells(_fused_cells(), page=1)
    # Âncora fundida: banda do segundo código abre o grupo 50000030
    # na linha 7, cobrindo 7-8 até a próxima âncora.
    assert _row_group(rows, 7) == ("50000030", "recovered_fused_anchor")
    assert _row_group(rows, 8)[0] == "50000030"
    # Grupo anterior mantém suas linhas.
    assert _row_group(rows, 4)[0] == "50000020"
    assert _row_group(rows, 6)[0] == "50000020"
    # Âncoras declaradas inalteradas.
    assert _row_group(rows, 1)[0] == "50000010"
    assert _row_group(rows, 9)[0] == "50000040"
    # Linha sem prova continua UNKNOWN.
    assert _row_group(rows, 3)[1] == "y_anchor_nearest"


def test_fused_anchor_second_group_code_recovered_letter_prefixed():
    rows, _ = rows_from_native_cells(
        _fused_cells(fragment_letter="B"), page=1
    )
    # A linha que hospeda o fragmento letra+código é a linha de
    # transição real (como "B 50233813" em 90264128): banda
    # mista → band_rehome_boundary → UNKNOWN preservado.
    assert _row_group(rows, 7) == ("50000030", "band_rehome_boundary")
    # Linhas seguintes entram no grupo recuperado com evidência
    # estrutural.
    assert _row_group(rows, 8) == ("50000030", "recovered_fused_anchor")


def test_fragment_with_component_code_never_anchors():
    """Fragmento letra+código cujo código É componente da tabela
    não pode virar âncora — par item/componente, não conjunto."""
    cells = _fused_cells(fragment_letter="B")
    for c in cells:
        if c.get("line_texts"):
            c["text"] = "50000020 B 10000007"
            c["line_texts"] = ["50000020", "B 10000007"]
    rows, _ = rows_from_native_cells(cells, page=1)
    assert _row_group(rows, 7)[0] == "50000020"
    assert _row_group(rows, 8)[0] == "50000020"


def test_fragment_repeating_parent_code_does_not_split_group():
    """Fragmento do próprio código-âncora (rotulo/banda duplicada)
    não subdivide o grupo."""
    cells = _fused_cells()
    for c in cells:
        if c.get("line_texts"):
            c["text"] = "50000020 50000020"
            c["line_texts"] = ["50000020", "50000020"]
    rows, _ = rows_from_native_cells(cells, page=1)
    assert _row_group(rows, 7)[0] == "50000020"
    assert _row_group(rows, 8)[0] == "50000020"


def test_orphan_group_code_token_anchors_uncovered_rows():
    cells = _fused_cells()
    marker_tokens = [
        {
            "raw_text": "50000050",
            "normalized_text": "50000050",
            "bounding_box_px": _quad(43, 312, 118, 333),
            "page": 1,
        }
    ]
    cells += _comp(11, "AA", "1", "10000011", 330)
    rows, _ = rows_from_native_cells(
        cells, page=1, marker_tokens=marker_tokens
    )
    assert _row_group(rows, 11)[0] == "50000050"
    assert _row_group(rows, 11)[1] == "recovered_token_anchor"


def test_orphan_token_never_splits_proven_block():
    """Código solto na coluna-pai não divide bloco já provado:
    linhas cobertas por âncora estrutural ficam intactas."""
    cells = _fused_cells()
    marker_tokens = [
        {
            "raw_text": "50000060",
            "normalized_text": "50000060",
            "bounding_box_px": _quad(43, 30, 118, 51),
            "page": 1,
        }
    ]
    rows, _ = rows_from_native_cells(
        cells, page=1, marker_tokens=marker_tokens
    )
    assert _row_group(rows, 1)[0] == "50000010"
    assert _row_group(rows, 2)[0] == "50000010"


def test_orphan_token_outside_parent_column_band_ignored():
    cells = _fused_cells()
    marker_tokens = [
        {
            "raw_text": "50000070",
            "normalized_text": "50000070",
            "bounding_box_px": _quad(600, 312, 680, 333),
            "page": 1,
        }
    ]
    cells += _comp(11, "AA", "1", "10000011", 330)
    rows, _ = rows_from_native_cells(
        cells, page=1, marker_tokens=marker_tokens
    )
    assert _row_group(rows, 11)[0] != "50000070"


def test_orphan_component_code_token_ignored():
    cells = _fused_cells()
    marker_tokens = [
        {
            "raw_text": "10000007",
            "normalized_text": "10000007",
            "bounding_box_px": _quad(43, 312, 118, 333),
            "page": 1,
        }
    ]
    cells += _comp(11, "AA", "1", "10000011", 330)
    rows, _ = rows_from_native_cells(
        cells, page=1, marker_tokens=marker_tokens
    )
    assert _row_group(rows, 11)[0] != "10000007"
