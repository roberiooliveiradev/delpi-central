"""G22 — drift entre token_cluster e native_table_cells (job real MCP).

Dois defeitos provados no caminho nativo do desenho 90263680:

1. ``regions.component_table.box_px`` herdava o crop hierárquico de
   colunas de código (``rmax + 0.18w``) e cortava a coluna de descrição
   → SLANet recebia raster sem a coluna → células vazias → linhas
   nativas substituíam as token-cluster sem descrição.
2. ``_anchor_description`` só aceitava célula irmã ``rowspan>1`` → PI
   de linha única (âncora ``column_span``) nunca recebia
   ``parent_group_description``, mesmo com a célula
   ``parent_description`` tipada ao lado.
"""
import json
from pathlib import Path

from engineering_app.application.drawing.understanding import (
    build_understanding,
    rows_from_native_cells,
)

FIXTURE = (
    Path(__file__).parent / "fixtures" / "g20_90263680_ocr_tokens.json"
)


_COL_X = {0: (98, 300), 1: (300, 600), 2: (630, 700),
          3: (720, 780), 4: (800, 905), 5: (915, 1430)}


def _cell(row, col, text, rowspan=1, y0=0, y1=10):
    x0, x1 = _COL_X[col]
    return {
        "row": row,
        "col": col,
        "text": text,
        "rowspan": rowspan,
        "colspan": 1,
        "bounding_box_px": [x0, y0, x1, y0, x1, y1, x0, y1],
        "token_centers": [[(x0 + x1) / 2, (y0 + y1) / 2]],
    }


def _delpi_cells():
    """Grade nativa do layout DELPI real (SLANet pós-crop corrigido)."""
    cells = [
        _cell(0, 0, "Código"), _cell(0, 1, "Descrição"),
        _cell(0, 2, "Item"), _cell(0, 3, "QTD."),
        _cell(0, 4, "Comp."), _cell(0, 5, "Descrição"),
    ]
    y = 20
    # PI de linha única — rowspan=1 em todas as células.
    cells += [
        _cell(1, 0, "50213206", y0=y, y1=y + 20),
        _cell(1, 1, "CA18BRAN-00512/10/10-0000-0000", y0=y, y1=y + 20),
        _cell(1, 2, "A", y0=y, y1=y + 20),
        _cell(1, 3, "1", y0=y, y1=y + 20),
        _cell(1, 4, "10380040", y0=y, y1=y + 20),
        _cell(1, 5, "CABO EPR 125/150°C 18AWG BN", y0=y, y1=y + 20),
    ]
    y += 20
    cells += [
        _cell(2, 0, "50213207", y0=y, y1=y + 20),
        _cell(2, 1, "CA18PRET-00512/10/10-0000-0000", y0=y, y1=y + 20),
        _cell(2, 2, "B", y0=y, y1=y + 20),
        _cell(2, 3, "1", y0=y, y1=y + 20),
        _cell(2, 4, "10380035", y0=y, y1=y + 20),
        _cell(2, 5, "CABO EPR 125/150°C 18AWG PT", y0=y, y1=y + 20),
    ]
    y += 20
    # PI mesclado cobrindo três linhas de componente.
    cells += [
        _cell(3, 0, "50233507", rowspan=3, y0=y, y1=y + 60),
        _cell(3, 1, "CA18MARR-00152/10/06-0000-0110", rowspan=3,
              y0=y, y1=y + 60),
        _cell(3, 2, "C", y0=y, y1=y + 20),
        _cell(3, 3, "1", y0=y, y1=y + 20),
        _cell(3, 4, "10080136", y0=y, y1=y + 20),
        _cell(3, 5, "TERM. BANDEIRA 6,3X0,8", y0=y, y1=y + 20),
        _cell(4, 2, "D", y0=y + 20, y1=y + 40),
        _cell(4, 3, "1", y0=y + 20, y1=y + 40),
        _cell(4, 4, "10090010", y0=y + 20, y1=y + 40),
        _cell(4, 5, "ISOLADOR NYLON 90° 6.3", y0=y + 20, y1=y + 40),
        _cell(5, 2, "E", y0=y + 40, y1=y + 60),
        _cell(5, 3, "1", y0=y + 40, y1=y + 60),
        _cell(5, 4, "10380042", y0=y + 40, y1=y + 60),
        _cell(5, 5, "CABO EPR 125/150°C 18AWG MR", y0=y + 40, y1=y + 60),
    ]
    y += 60
    cells += [
        _cell(6, 0, "50233508", rowspan=3, y0=y, y1=y + 60),
        _cell(6, 1, "CA18MABR-00242/10/06-0000-0110", rowspan=3,
              y0=y, y1=y + 60),
        _cell(6, 2, "C", y0=y, y1=y + 20),
        _cell(6, 3, "1", y0=y, y1=y + 20),
        _cell(6, 4, "10080136", y0=y, y1=y + 20),
        _cell(6, 5, "TERM. BANDEIRA 6,3X0,8", y0=y, y1=y + 20),
        _cell(7, 2, "D", y0=y + 20, y1=y + 40),
        _cell(7, 3, "1", y0=y + 20, y1=y + 40),
        _cell(7, 4, "10090010", y0=y + 20, y1=y + 40),
        _cell(7, 5, "ISOLADOR NYLON 90° 6.3", y0=y + 20, y1=y + 40),
        _cell(8, 2, "F", y0=y + 40, y1=y + 60),
        _cell(8, 3, "1", y0=y + 40, y1=y + 60),
        _cell(8, 4, "10380111", y0=y + 40, y1=y + 60),
        _cell(8, 5, "CABO EPR 125/150°C 18AWG MRBN", y0=y + 40,
              y1=y + 60),
    ]
    return cells


def test_single_row_pi_gets_parent_group_description():
    """RQ22-01/AC22-01: PI rowspan=1 associa a descrição da célula
    parent_description ao grupo — antes só células rowspan>1
    serviam de fonte."""
    rows, _ = rows_from_native_cells(_delpi_cells(), page=1)
    by_code = {r["component_code"]: r for r in rows}
    assert by_code["10380040"]["parent_group_candidate"] == "50213206"
    assert (
        by_code["10380040"]["parent_group_description"]
        == "CA18BRAN-00512/10/10-0000-0000"
    )
    assert (
        by_code["10380035"]["parent_group_description"]
        == "CA18PRET-00512/10/10-0000-0000"
    )
    assert (
        by_code["10380111"]["parent_group_description"]
        == "CA18MABR-00242/10/06-0000-0110"
    )


def test_merged_description_cell_still_preferred():
    """Invariante: célula rowspan>1 permanece a fonte preferida —
    o fallback rowspan=1 não pode sombreá-la."""
    cells = _delpi_cells()
    rows, _ = rows_from_native_cells(cells, page=1)
    for code in ("10080136", "10090010", "10380042"):
        row = next(
            r for r in rows
            if r["component_code"] == code
            and r["parent_group_candidate"] == "50233507"
        )
        assert (
            row["parent_group_description"]
            == "CA18MARR-00152/10/06-0000-0110"
        )


def test_component_description_never_becomes_group_description():
    """Negativo: sem coluna parent_description tipada, a descrição do
    componente não pode ser promovida a descrição do grupo."""
    cells = [
        _cell(0, 0, "Comp."), _cell(0, 1, "Descrição"),
        _cell(1, 0, "10080136"), _cell(1, 1, "TERM. BANDEIRA"),
        _cell(2, 0, "10090010"), _cell(2, 1, "ISOLADOR NYLON"),
    ]
    rows, _ = rows_from_native_cells(cells, page=1)
    for r in rows:
        assert not r.get("parent_group_description")


def test_region_crop_covers_typed_description_column():
    """RQ22-02/AC22-02: regions.component_table.box_px deve cobrir a
    coluna tipada de descrição (tokens até x≈1430) — o crop
    hierárquico por colunas de código parava em x≈1148."""
    tokens = json.loads(FIXTURE.read_text(encoding="utf-8"))
    u = build_understanding(
        tokens, document_hash="g22", page=1, product_code="90263680",
        render_size_px=(1653, 2339),
    )
    region = next(
        r for r in u["regions"] if r["type"] == "component_table"
    )
    desc_x_max = max(
        (t.get("bounding_box_px") or [0] * 8)[2]
        for t in tokens
        if "CABO" in str(t.get("raw_text") or t.get("text") or "").upper()
        or "TERM" in str(t.get("raw_text") or t.get("text") or "").upper()
        or "ISOLADOR" in str(t.get("raw_text") or t.get("text") or "").upper()
    )
    assert region["box_px"][2] >= desc_x_max - 1, (
        region["box_px"],
        desc_x_max,
    )


def test_typed_extent_excludes_untyped_noise():
    """Sibling/negativo da P12: células não tipadas (ruído de carimbo
    absorvido) não podem expandir o envelope tipado."""
    from engineering_app.application.drawing.understanding import (
        _typed_cells_extent,
    )

    rows = [
        {
            "cells": [
                {"col": 0, "bounding_box_px": [100, 100, 200, 100, 200, 130, 100, 130]},
                {"col": 1, "bounding_box_px": [900, 100, 1400, 100, 1400, 130, 900, 130]},
                {"col": 9, "bounding_box_px": [2000, 100, 2200, 100, 2200, 130, 2000, 130]},
            ],
            "col_types": {"0": "component_code", "1": "description"},
        }
    ]
    extent = _typed_cells_extent(rows, {0: "component_code", 1: "description"})
    assert extent is not None
    assert extent[2] == 1400  # ruído x≈2200 fora — coluna não tipada
