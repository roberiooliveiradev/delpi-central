"""DEC-VAL-042 — gate conservador de células nativas + descrição."""
from __future__ import annotations

from engineering_app.application.drawing.understanding import (
    apply_native_table_observations,
    native_cells_preferable,
    rows_from_native_cells,
)


def _bbox(x0: float, y0: float, x1: float, y1: float) -> list[float]:
    return [x0, y0, x1, y0, x1, y1, x0, y1]


def _cell(
    row: int,
    col: int,
    text: str,
    *,
    rowspan: int = 1,
    x0: float = 0.0,
    y0: float = 0.0,
    x1: float = 40.0,
    y1: float = 20.0,
    page: int = 1,
) -> dict:
    return {
        "row": row,
        "col": col,
        "rowspan": rowspan,
        "colspan": 1,
        "text": text,
        "page": page,
        "bounding_box_px": _bbox(x0, y0, x1, y1),
        "token_centers": [[(x0 + x1) / 2.0, (y0 + y1) / 2.0]],
    }


# Geometria espelhando a banda medida do 90264026: grupo à esquerda,
# item/qtd/código/descrição em colunas à direita (várias amostras item
# para formar role_band e classificar contexto de grupo).
NATIVE_90264026_LIKE = [
    _cell(0, 0, "90264026 CHCIOTE DE LIGACAO", x0=60, y0=1546, x1=290, y1=1678),
    _cell(0, 2, "A", rowspan=3, x0=370, y0=1570, x1=400, y1=1590),
    _cell(0, 5, "1", x0=420, y0=1570, x1=450, y1=1590),
    _cell(0, 6, "10080001", x0=480, y0=1570, x1=560, y1=1590),
    _cell(
        0, 7, "TERM. BANDEIRA 6,3X0,8 0,5-1,5MM NU UL ALTURA 16MM",
        x0=600, y0=1570, x1=1200, y1=1590,
    ),
    _cell(1, 2, "F", x0=370, y0=1600, x1=400, y1=1620),
    _cell(1, 5, "1", x0=420, y0=1600, x1=450, y1=1620),
    _cell(1, 6, "10081047", x0=480, y0=1600, x1=560, y1=1620),
    _cell(
        1, 7, "TERM. OLHAL M10 ESTANHADO",
        x0=600, y0=1600, x1=1200, y1=1620,
    ),
    _cell(3, 3, "B", x0=370, y0=1635, x1=400, y1=1655),
    _cell(3, 4, "1", x0=420, y0=1635, x1=450, y1=1655),
    _cell(3, 5, "10090010", x0=480, y0=1635, x1=560, y1=1655),
    _cell(
        3, 6, "ISOLADOR NYLON 90 PRETA ABERTA",
        x0=600, y0=1635, x1=1200, y1=1655,
    ),
    _cell(4, 3, "C", x0=370, y0=1665, x1=400, y1=1685),
    _cell(4, 4, "1", x0=420, y0=1665, x1=450, y1=1685),
    _cell(4, 5, "10110020", x0=480, y0=1665, x1=560, y1=1685),
    _cell(
        4, 6, "ETIQUETA ACETATO DE RAYON N7",
        x0=600, y0=1665, x1=1200, y1=1685,
    ),
]


def test_red_to_green_span_conflict_applies_native_and_descriptions():
    """RQ-042-01/02/03 — span_conflict localizado não descarta grade útil."""
    rows, _ = rows_from_native_cells(NATIVE_90264026_LIKE, page=1)
    by_item = {
        str(r.get("item") or "").upper(): r
        for r in rows
        if r.get("item")
    }
    assert by_item["B"]["component_code"] == "10090010"
    assert "90264026" not in str(by_item["B"]["component_code"])
    assert "ISOLADOR" in str(by_item["B"].get("description") or "")
    assert "CHCIOTE" not in str(by_item["B"].get("description") or "")
    assert "BANDEIRA" in str(by_item["A"].get("description") or "")

    fallback = [
        {
            "page": 1,
            "item": "B",
            "quantity": "1",
            "component_code": "90264026 10090010",
            "description": None,
            "association_status": "FIELD_IDENTIFIED",
        }
    ]
    updated = apply_native_table_observations(
        {
            "component_table": {"rows": list(fallback), "row_count": 1},
            "limitations": [],
        },
        [{
            "region_type": "component_table",
            "page": 1,
            "result": {
                "cells": NATIVE_90264026_LIKE,
                "tables": [{
                    "structure_consistent": False,
                    "structure_limitations": ["span_conflict"],
                }],
                "limitations": ["span_conflict"],
            },
        }],
    )
    out = (updated.get("component_table") or {}).get("rows") or []
    by_item = {
        str(r.get("item") or "").upper(): r
        for r in out
        if r.get("item")
    }
    assert by_item["B"]["component_code"] == "10090010"
    assert "ISOLADOR" in str(by_item["B"].get("description") or "")
    assert (updated.get("component_table") or {}).get(
        "topology_source"
    ) == "native_table_cells"
    lim = " ".join(updated.get("limitations") or [])
    assert "span_conflict_tolerated" in lim
    assert "structure_incomplete" not in lim


def test_negative_hard_limitation_keeps_fallback():
    """Spans + bbox mismatch permanecem rejeitados."""
    fallback = [{
        "page": 1,
        "item": "B",
        "component_code": "10090010",
        "description": "OK",
    }]
    updated = apply_native_table_observations(
        {
            "component_table": {"rows": list(fallback), "row_count": 1},
            "limitations": [],
        },
        [{
            "region_type": "component_table",
            "page": 1,
            "result": {
                "cells": NATIVE_90264026_LIKE,
                "tables": [{
                    "structure_consistent": False,
                    "structure_limitations": [
                        "span_conflict", "bbox_count_mismatch",
                    ],
                }],
            },
        }],
    )
    rows = (updated.get("component_table") or {}).get("rows") or []
    assert rows[0]["component_code"] == "10090010"
    assert "structure_incomplete" in " ".join(updated.get("limitations") or [])


def test_negative_native_worse_fusion_keeps_fallback():
    """Grade nativa com mais fusões que o fallback não é promovida."""
    fused_native = [
        _cell(0, 0, "A", x0=100, y0=10, x1=120, y1=30),
        _cell(0, 1, "1", x0=140, y0=10, x1=160, y1=30),
        _cell(0, 2, "10080192 10090316", x0=180, y0=10, x1=280, y1=30),
        _cell(1, 0, "B", x0=100, y0=40, x1=120, y1=60),
        _cell(1, 1, "1", x0=140, y0=40, x1=160, y1=60),
        _cell(1, 2, "10090010 10090011", x0=180, y0=40, x1=280, y1=60),
        _cell(2, 0, "C", x0=100, y0=70, x1=120, y1=90),
        _cell(2, 1, "1", x0=140, y0=70, x1=160, y1=90),
        _cell(2, 2, "10110020 10110021", x0=180, y0=70, x1=280, y1=90),
        _cell(3, 0, "D", x0=100, y0=100, x1=120, y1=120),
        _cell(3, 1, "1", x0=140, y0=100, x1=160, y1=120),
        _cell(3, 2, "10120030 10120031", x0=180, y0=100, x1=280, y1=120),
    ]
    native_rows, _ = rows_from_native_cells(fused_native, page=1)
    fallback = [
        {"page": 1, "item": "A", "component_code": "10080192"},
        {"page": 1, "item": "B", "component_code": "10090010"},
    ]
    apply, reason = native_cells_preferable(
        consistent=False,
        structure_limitations=["span_conflict"],
        native_rows=native_rows,
        fallback_rows=fallback,
    )
    assert apply is False
    assert reason == "structure_incomplete"


def test_negative_group_description_not_item_description():
    rows, _ = rows_from_native_cells(NATIVE_90264026_LIKE, page=1)
    by_item = {
        str(r.get("item") or "").upper(): r
        for r in rows
        if r.get("item")
    }
    for item in ("A", "B", "C"):
        desc = str(by_item[item].get("description") or "")
        assert "90264026" not in desc
        assert "CHCIOTE" not in desc


def test_negative_always_use_native_is_not_the_policy():
    """Gate nunca reduz a ``not error`` — exige evidência."""
    apply, reason = native_cells_preferable(
        consistent=False,
        structure_limitations=["span_conflict", "empty_structure"],
        native_rows=[{
            "item": "B",
            "component_code": "10090010",
            "description": "X",
        }],
        fallback_rows=[],
    )
    assert apply is False
    assert reason == "structure_incomplete"
