"""EVA VAL-01 — fronteira de âncoras de grupo deslocadas (Issue #131).

Classe de defeito observada em desenho real: a SLANet declara a
célula mesclada do conjunto uma linha tarde (índice de linha e/ou
rowspan deslocados em relação à célula física). A herança
sequencial ``arow <= row < arow + span`` então:

- perde a **primeira linha real** do grupo, que permanece sob a
  âncora anterior ou fica ``UNKNOWN`` por proximidade;
- absorve a **primeira linha do grupo seguinte**, publicando-a
  como filha legítima ``IDENTIFIED`` do pai errado.

Evidência corretiva estrutural e generalista: o texto de uma
célula mesclada é centrado verticalmente nela — o centróide dos
tokens da âncora marca o centro da janela real de linhas cobertas.
Janelas candidatas a um passo do declarado são pontuadas pela
distância entre o centro da extensão de bandas coberta e esse
centróide; a âncora só se move quando a janela alternativa é
materialmente melhor centrada e não deixa banda povoada órfã.

Códigos e geometria são sintéticos; nenhum valor vem do desenho
que motivou a correção.
"""
from __future__ import annotations

from engineering_app.application.drawing.understanding import (
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


def _child_cells(row, cy, item, code):
    """Linha filha na grade: item, quantidade, código, descrição.

    ``token_centers`` marca a banda real da linha (posição OCR), o
    que o polígono SLANet aproxima com folga.
    """
    tcs = [[410.0, cy - 8.0], [410.0, cy + 8.0]]
    return [
        _cell(row, 2, item, _quad(380, cy - 16, 440, cy + 16),
              token_centers=tcs),
        _cell(row, 3, "1", _quad(445, cy - 16, 480, cy + 16),
              token_centers=[[460.0, cy]]),
        _cell(row, 4, code, _quad(490, cy - 16, 560, cy + 16),
              token_centers=[[525.0, cy]]),
        _cell(row, 5, f"DESC {item}", _quad(570, cy - 16, 860, cy + 16),
              token_centers=[[700.0, cy]]),
    ]


def _anchor(row, code, cy, *, rowspan, top, bottom):
    return [
        _cell(row, 0, code, _quad(60, top, 150, bottom),
              rowspan=rowspan,
              token_centers=[[100.0, cy]]),
        _cell(row, 1, f"DESC {code}", _quad(160, top, 370, bottom),
              rowspan=rowspan,
              token_centers=[[260.0, cy]]),
    ]


G1, G2, G3 = "50000001", "50000002", "50000003"

# Bandas das linhas filhas (pitch 38): células reais ladrilham
# r1-3 → G1, r4-6 → G2, r9-11 → G3. As âncoras G1 e G2 são
# declaradas uma linha tarde — exatamente o deslocamento medido
# no desenho real; G3 já está alinhada (controle negativo).
ROWS = [
    (1, 115, "AA", "10000001"),
    (2, 153, "AB", "10000002"),
    (3, 191, "AC", "10000003"),
    (4, 229, "AD", "10000004"),
    (5, 267, "AE", "10000005"),
    (6, 305, "AF", "10000006"),
    (7, 343, "AG", "10000007"),
    (9, 419, "AJ", "10000009"),
    (10, 457, "AK", "10000010"),
    (11, 495, "AL", "10000011"),
]


def _offset_anchor_cells():
    cells: list[dict] = []
    # G1 real cobre r1-3 (centro ~153); SLANet declara em r2, rs=3.
    cells += _anchor(2, G1, 153, rowspan=3, top=118, bottom=200)
    # G2 real cobre r4-6 (centro ~267); SLANet declara em r5, rs=3.
    cells += _anchor(5, G2, 267, rowspan=3, top=235, bottom=310)
    # G3 real cobre r9-11 e a âncora declarada já bate (controle).
    cells += _anchor(9, G3, 455, rowspan=3, top=415, bottom=500)
    for r, cy, item, code in ROWS:
        cells += _child_cells(r, cy, item, code)
    return cells


def _occurrences(cells=None):
    rows, _ = rows_from_native_cells(cells or _offset_anchor_cells(),
                                     page=1)
    return drawing_structure_occurrences(rows, product_code="90000000")


def _by_item(occs):
    return {o["item"]: o for o in occs}


def test_first_child_row_is_not_stolen_by_next_group():
    """Primeira linha do bloco seguinte não pode virar filha da
    âncora anterior."""
    occs = _by_item(_occurrences())
    assert occs["AD"]["parent_code"] == G2
    assert occs["AD"]["parent_state"] == "IDENTIFIED"


def test_own_first_row_keeps_structural_parent():
    """A primeira linha real do grupo herda a própria âncora."""
    occs = _by_item(_occurrences())
    assert occs["AA"]["parent_code"] == G1
    assert occs["AA"]["parent_state"] == "IDENTIFIED"


def test_row_after_last_covered_row_not_promoted():
    """Linha fora da célula não pode ser absorvida como filha
    IDENTIFIED — a incerteza real permanece UNKNOWN (fail-closed)."""
    occs = _by_item(_occurrences())
    assert not (
        occs["AG"]["parent_code"] == G2
        and occs["AG"]["parent_state"] == "IDENTIFIED"
    )
    assert occs["AG"]["parent_state"] == "UNKNOWN"


def test_sibling_rows_keep_correct_parents():
    occs = _by_item(_occurrences())
    for item in ("AB", "AC"):
        assert occs[item]["parent_code"] == G1
        assert occs[item]["parent_state"] == "IDENTIFIED"
    for item in ("AE", "AF"):
        assert occs[item]["parent_code"] == G2
        assert occs[item]["parent_state"] == "IDENTIFIED"


def test_aligned_anchor_is_not_shifted():
    """Âncora já alinhada à banda da primeira linha não se move."""
    occs = _by_item(_occurrences())
    for item in ("AJ", "AK", "AL"):
        assert occs[item]["parent_code"] == G3
        assert occs[item]["parent_state"] == "IDENTIFIED"


def test_no_duplicate_occurrences():
    """O realinhamento não pode duplicar a mesma linha física."""
    occs = _occurrences()
    keys = [(o["row"], o["item"], o["component_code"]) for o in occs]
    assert len(keys) == len(set(keys))


# --- Classe de poluição: células vazias com polígono de célula
# mesclada inflando a banda de conteúdo (Issue #131, residual
# AE→50225702). Uma célula sem texto e sem tokens não pode provar
# uma banda de conteúdo — seu polígono SLANet herda a altura da
# célula mesclada e mascara o desalinhamento da âncora.

P1, P2 = "60000001", "60000002"


def _polluted_anchor_cells(*, with_empty_cells: bool = True):
    """Âncora declarada uma linha tarde (r2 rs2, real r1-3) com
    células vazias cujos polígonos cobrem a altura da célula
    mesclada — mesmo sinal degenerado do caso real."""
    cells: list[dict] = []
    # P1 real cobre r1-3 (centro ~153); SLANet declara r2 rs2.
    cells += _anchor(2, P1, 153, rowspan=2, top=99, bottom=207)
    # P2 real cobre r4-6, já alinhado (controle de fronteira).
    cells += _anchor(4, P2, 267, rowspan=3, top=215, bottom=320)
    for r, cy, item, code in (
        (1, 115, "AX", "20000001"),
        (2, 153, "AY", "20000002"),
        (3, 191, "AZ", "20000003"),
        (4, 229, "BA", "20000004"),
        (5, 267, "BB", "20000005"),
        (6, 305, "BC", "20000006"),
    ):
        cells += _child_cells(r, cy, item, code)
    if with_empty_cells:
        # Células vazias em r2: sem texto, sem token_centers —
        # polígono cobre a extensão da célula mesclada inteira.
        for col in (3, 4):
            cells.append(
                _cell(2, col, "", _quad(450, 99, 560, 207))
            )
    return cells


def test_empty_cell_polygon_does_not_pollute_band_signal():
    """O realinhamento deve enxergar a janela real mesmo com
    células vazias de polígono inflado — a primeira linha do grupo
    volta para a própria âncora."""
    occs = _by_item(_occurrences(_polluted_anchor_cells()))
    assert occs["AX"]["parent_code"] == P1
    assert occs["AX"]["parent_state"] == "IDENTIFIED"
    # Grupo seguinte preservado — a correção não invade.
    for item in ("BA", "BB", "BC"):
        assert occs[item]["parent_code"] == P2
        assert occs[item]["parent_state"] == "IDENTIFIED"


def test_empty_cells_do_not_change_table_structure():
    """Células vazias continuam existindo na topologia; só saem do
    sinal de banda de conteúdo."""
    rows, _ = rows_from_native_cells(_polluted_anchor_cells(), page=1)
    by_row = {r["row"]: r for r in rows}
    assert 2 in by_row  # a linha continua existindo
    occs = _by_item(_occurrences(_polluted_anchor_cells()))
    assert not (occs["AY"]["parent_code"] == P2)


def test_textless_cell_with_bbox_still_bounds_when_it_has_tokens():
    """Célula com tokens mas sem texto continua marcando banda —
    a exclusão só se aplica a células sem qualquer evidência."""
    cells = _polluted_anchor_cells(with_empty_cells=False)
    # Célula "vazia de texto" mas com tokens vinculados em r2.
    cells.append(
        _cell(2, 3, "", _quad(450, 140, 560, 168),
              token_centers=[[500.0, 154.0]])
    )
    occs = _by_item(_occurrences(cells))
    assert occs["AX"]["parent_code"] == P1
    assert occs["AX"]["parent_state"] == "IDENTIFIED"
