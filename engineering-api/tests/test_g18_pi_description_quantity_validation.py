"""G18 — decoder PI 50xx, normalização MI/MT/PC e integração no
comparador (Doc 119 §94.20, caso 90263680).

Sem OCR, sem rede — fixtures reproduzem o shape real de
``flatten_bom_occurrences`` e ``component_table.rows``.
"""

from __future__ import annotations

from engineering_app.application.drawing.bom_structure_comparator import (
    compare_bom_to_drawing,
)
from engineering_app.application.drawing.description_rules import (
    diff_pi50_descriptions,
    is_pi50_code,
    parse_pi50_segments,
)
from engineering_app.application.drawing.quantity_normalization import (
    compare_quantity,
    normalize_bom_consumption,
)

PRODUCT = "90263680"


# ------------------------------------------------------------------
# RQ06 — decoder segment-wise PI 50xx
# ------------------------------------------------------------------


def test_pi50_parse_full_segments():
    seg = parse_pi50_segments("CB18MARR-00152/10/06-0000-3610")
    assert seg == {
        "isolation_prefix": "CB",
        "isolation_material": "EPR",
        "gauge": "18",
        "color": "MARR",
        "length_mm": 152,
        "decape_left_mm": 10,
        "decape_right_mm": 6,
        "terminal_left": "00",
        "isolator_left": "00",
        "terminal_right": "36",
        "isolator_right": "10",
    }


def test_pi50_parse_decimal_gauge_and_terminal_pairs():
    seg = parse_pi50_segments(
        "CB1,50VERD-00255/06/06-6314-0111"
    )
    assert seg["gauge"] == "1,50"
    assert seg["length_mm"] == 255
    assert seg["terminal_left"] == "63"
    assert seg["isolator_left"] == "14"
    assert seg["terminal_right"] == "01"
    assert seg["isolator_right"] == "11"


def test_pi50_parse_rejects_non_normative():
    assert parse_pi50_segments("CABO FLEXIVEL 2,5MM AZUL") is None
    assert parse_pi50_segments(None) is None
    assert is_pi50_code("50233507") and not is_pi50_code("90263680")


def test_pi50_diff_flags_only_different_segments():
    diff = diff_pi50_descriptions(
        observed="CA18MARR-00152/10/06-0000-0110",
        expected="CB18MARR-00152/10/06-0000-3610",
    )
    assert diff["status"] == "SEGMENT_DIFFERENCES"
    names = {d["segment"] for d in diff["segment_differences"]}
    assert names == {"isolation_prefix", "terminal_right"}


def test_pi50_diff_match_and_inconclusive():
    same = "CB18BRAN-00512/10/10-0000-0000"
    assert diff_pi50_descriptions(observed=same, expected=same)[
        "status"
    ] == "SEGMENT_MATCH"
    bad = diff_pi50_descriptions(
        observed="TEXTO LIVRE", expected=same
    )
    assert bad["status"] == "INCONCLUSIVE"


# ------------------------------------------------------------------
# RQ07 — normalização governada MI/MT/PC
# ------------------------------------------------------------------


def test_normalize_mt_under_mi_basis():
    n = normalize_bom_consumption(512, "MT", pa_unit="MI")
    assert n["status"] == "NORMALIZED"
    assert n["value_per_piece"] == 0.512
    assert n["value_per_piece_mm"] == 512.0
    assert "512 MT / 1000" in n["formula"]


def test_normalize_pc_under_mi_basis():
    n = normalize_bom_consumption(1000, "PC", pa_unit="MI")
    assert n["status"] == "NORMALIZED"
    assert n["value_per_piece"] == 1.0


def test_normalize_not_comparable_cases():
    assert normalize_bom_consumption(512, "MT", pa_unit="UN")[
        "status"
    ] == "NOT_COMPARABLE"
    assert normalize_bom_consumption(512, "MT", pa_unit=None)[
        "status"
    ] == "NOT_COMPARABLE"
    assert normalize_bom_consumption(None, "MT", pa_unit="MI")[
        "status"
    ] == "NOT_COMPARABLE"
    # unidade sem regra aprovada
    assert normalize_bom_consumption(5, "CX", pa_unit="MI")[
        "status"
    ] == "NOT_COMPARABLE"


def test_compare_quantity_pc_match_and_conflict():
    n = normalize_bom_consumption(1000, "PC", pa_unit="MI")
    assert compare_quantity(
        drawing_quantity=1, drawing_unit="PC", normalization=n
    )["result"] == "MATCH_CANDIDATE"
    assert compare_quantity(
        drawing_quantity=2, drawing_unit="PC", normalization=n
    )["result"] == "CONFLICT_CANDIDATE"


def test_compare_quantity_cable_length_not_meter():
    # QTD=1 do desenho nunca vira "1 metro de cabo".
    n = normalize_bom_consumption(512, "MT", pa_unit="MI")
    c = compare_quantity(
        drawing_quantity=1, drawing_unit=None, normalization=n
    )
    assert c["result"] == "NOT_COMPARABLE"


# ------------------------------------------------------------------
# Integração — atributo pi_description + segment_diff no comparador
# ------------------------------------------------------------------


def _bom_occ(code, parent, depth, desc, qty, unit):
    return {
        "occurrence_id": f"O-{code}-{depth}-{qty}",
        "component_code": code,
        "component_type": "PI" if code.startswith("5") else "MP",
        "component_description": desc,
        "parent_code": parent,
        "depth": depth,
        "path": f"{PRODUCT}/{code}",
        "quantity_raw": qty,
        "unit_raw": unit,
    }


def _table_row(
    code, desc, parent_desc, qty, unit, page=1, parent="50233507"
):
    return {
        "row": 1,
        "y_px": 100.0,
        "component_code": code,
        "description": desc,
        "quantity": qty,
        "unit": unit,
        "parent_group_candidate": parent,
        "parent_group_source": "rowspan_anchor",
        "parent_group_description": parent_desc,
        "cells": [
            {
                "text": code,
                "col": 0,
                "row": 1,
                "col_type": "component_code",
                "page": page,
            }
        ],
    }


def _component_table(rows):
    return {
        "candidate": True,
        "rows": rows,
        "row_count": len(rows),
        "code_count": len(rows),
    }


def _find_attr(records, code, attr):
    for r in records:
        if r.get("component_code") == code:
            for a in r.get("attributes") or []:
                if a.get("attribute") == attr:
                    return a
    return None


def test_comparator_pi_description_segment_diff_90263680():
    """Caso real: desenho CA18…-0000-0110 × TOTVS CB18…-0000-3610."""
    bom = [
        _bom_occ(
            "50233507",
            PRODUCT,
            1,
            "CB18MARR-00152/10/06-0000-3610",
            1,
            "MI",
        ),
        _bom_occ(
            "10380042",
            "50233507",
            2,
            "CABO",
            152,
            "MT",
        ),
    ]
    table = _component_table(
        [
            _table_row(
                "10380042",
                "CABO",
                "CA18MARR-00152/10/06-0000-0110",
                1,
                None,
            )
        ]
    )
    report = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        pa_unit="MI",
    )
    vr = report["validation_report"]
    pi_attr = _find_attr(vr["occurrence_records"], "10380042", "pi_description")
    assert pi_attr["result"] == "CONFLICT_CANDIDATE"
    assert pi_attr["observed_value"] == "CA18MARR-00152/10/06-0000-0110"
    assert pi_attr["expected_value"] == "CB18MARR-00152/10/06-0000-3610"
    names = {d["segment"] for d in pi_attr["segment_differences"]}
    assert names == {"isolation_prefix", "terminal_right"}


def test_comparator_pi_description_match_and_missing():
    bom = [
        _bom_occ(
            "50213206",
            PRODUCT,
            1,
            "CB18BRAN-00512/10/10-0000-0000",
            1,
            "MI",
        ),
        _bom_occ("10380040", "50213206", 2, "CABO", 512, "MT"),
    ]
    # descrição observada idêntica → MATCH_CANDIDATE
    table = _component_table(
        [
            _table_row(
                "10380040",
                "CABO",
                "CB18BRAN-00512/10/10-0000-0000",
                1,
                None,
                parent="50213206",
            )
        ]
    )
    report = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        pa_unit="MI",
    )
    pi_attr = _find_attr(
        report["validation_report"]["occurrence_records"],
        "10380040",
        "pi_description",
    )
    assert pi_attr["result"] == "MATCH_CANDIDATE"
    # descrição do pai não observada → NOT_CHECKED (não divergência)
    table2 = _component_table(
        [
            _table_row(
                "10380040", "CABO", None, 1, None,
                parent="50213206",
            )
        ]
    )
    report2 = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table2,
        pa_unit="MI",
    )
    pi_attr2 = _find_attr(
        report2["validation_report"]["occurrence_records"],
        "10380040",
        "pi_description",
    )
    assert pi_attr2["result"] == "NOT_CHECKED"


def test_comparator_quantity_normalized_pc_match():
    bom = [
        _bom_occ(
            "50233507",
            PRODUCT,
            1,
            "CB18MARR-00152/10/06-0000-3610",
            1,
            "MI",
        ),
        _bom_occ("10080136", "50233507", 2, "TERMINAL", 1000, "PC"),
    ]
    table = _component_table(
        [
            _table_row(
                "10080136", "TERMINAL", None, 1, "PC",
                parent="50233507",
            )
        ]
    )
    report = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        pa_unit="MI",
    )
    qty_attr = _find_attr(
        report["validation_report"]["occurrence_records"],
        "10080136",
        "quantity",
    )
    assert qty_attr["result"] == "MATCH_CANDIDATE"
    assert qty_attr["normalization"]["value_per_piece"] == 1.0
    assert qty_attr["normalization"]["basis_source"]


def test_comparator_quantity_not_comparable_without_basis():
    bom = [
        _bom_occ(
            "50213207", PRODUCT, 1,
            "CB18PRET-00512/10/10-0000-0000", 1, "MI",
        ),
        _bom_occ("10380035", "50213207", 2, "CABO", 512, "MT"),
    ]
    table = _component_table(
        [
            _table_row(
                "10380035", "CABO", None, 1, None,
                parent="50213207",
            )
        ]
    )
    # sem pa_unit → sem regra → NOT_COMPARABLE (não divergência)
    report = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
    )
    qty_attr = _find_attr(
        report["validation_report"]["occurrence_records"],
        "10380035",
        "quantity",
    )
    assert qty_attr["result"] == "NOT_COMPARABLE"
    assert qty_attr["normalization"]["status"] == "NOT_COMPARABLE"
    # cabo com unidade MT: QTD do desenho é ocorrência — não comparável
    report2 = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        pa_unit="MI",
    )
    qty_attr2 = _find_attr(
        report2["validation_report"]["occurrence_records"],
        "10380035",
        "quantity",
    )
    assert qty_attr2["result"] == "NOT_COMPARABLE"


def test_comparator_segment_diff_on_item_description():
    """Quando a própria linha tipada traz descrição PI divergente."""
    bom = [
        _bom_occ(
            "50233507",
            PRODUCT,
            1,
            "CB18MARR-00152/10/06-0000-3610",
            1,
            "MI",
        )
    ]
    table = _component_table(
        [
            {
                "row": 1,
                "y_px": 50.0,
                "component_code": "50233507",
                "description": "CA18MARR-00152/10/06-0000-0110",
                "quantity": 1,
                "cells": [
                    {
                        "text": "50233507",
                        "col": 0,
                        "row": 1,
                        "col_type": "component_code",
                        "page": 1,
                    }
                ],
            }
        ]
    )
    report = compare_bom_to_drawing(
        product_code=PRODUCT,
        bom_occurrences=bom,
        component_table=table,
        pa_unit="MI",
    )
    desc_attr = _find_attr(
        report["validation_report"]["occurrence_records"],
        "50233507",
        "description",
    )
    assert desc_attr["result"] == "CONFLICT_CANDIDATE"
    names = {d["segment"] for d in desc_attr["segment_differences"]}
    assert names == {"isolation_prefix", "terminal_right"}
    # finding candidato nunca vira NC
    assert (
        report["validation_report"]["engineering_approval"]
        == "NOT_APPROVED"
    )
