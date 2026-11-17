"""E1/VAL-01 B3 — coerência visual balão × componente × tabela.

Cobre RQ-B3-01..06: atributos declarados extraídos das células da
linha com proveniência, classe visual observada independente da
expectativa (barra alongada saturada × compacta × mista), matriz
COMPATIBLE_CANDIDATE / CONFLICT_CANDIDATE / INCONCLUSIVE /
NOT_COMPARABLE, preservação de ambiguidades B2 e multiplicidade.
"""
from engineering_app.application.drawing.drawing_investigation import (
    build_balloon_table_validation,
)

SHA = "sha-b3"


def _cell(text, col, col_type=None):
    c = {
        "text": text, "col": col, "row": 0,
        "bounding_box_px": [0, 0, 10, 0, 10, 8, 0, 8],
        "confidence": 0.99, "page": 1,
    }
    if col_type:
        c["col_type"] = col_type
    return c


def _row(i, code, item, desc_cells):
    """Linha com células: item col1, código col3 (tipado), descrição
    nas colunas seguintes — layout observado nos três PDFs reais."""
    cells = [_cell(item, 1),
             _cell(code, 3, "component_code")]
    cells += [_cell(t, 4 + k) for k, t in enumerate(desc_cells)]
    return {
        "row": i, "page": 1,
        "fields": {"component_code": {"normalized_value": code}},
        "association_status": "FIELD_IDENTIFIED", "cells": cells,
    }


def _obs(ar, sat, hue=None, frac=0.0, semantics=None):
    o = {
        "aspect_ratio": ar, "sat_coverage": sat,
        "dominant_hue": hue, "dominant_hue_fraction": frac,
    }
    if semantics:
        o["fill_semantics"] = semantics
    return o


def _balloon(label, leader=None):
    return {
        "item_label": label, "normalized_label": label.upper(),
        "page": 1, "bounding_box_px": [10, 10, 40, 40],
        "token_bounding_box_px": [14, 14, 36, 36],
        "identification_method": "primitive_containment",
        "leader_line": leader,
    }


def _leader_single(obs=None, region=(0, 0, 400, 20), region_id="uleadtgt:0"):
    return {
        "state": "CANDIDATE", "segments_px": [[0, 50, 0, 80]],
        "endpoint_px": [50, 60],
        "target_state": "SINGLE_REGION",
        "target_region_id": region_id,
        "target_region_px": list(region),
        "target_observation": obs,
        "alternative_target_regions_px": [],
        "alternative_targets": [],
    }


def _leader_ambiguous(alts):
    return {
        "state": "CANDIDATE", "segments_px": [[0, 50, 0, 80]],
        "endpoint_px": [50, 60],
        "target_state": "AMBIGUOUS_REGIONS",
        "target_region_id": None, "target_region_px": None,
        "target_observation": None,
        "alternative_target_regions_px": [a[0] for a in alts],
        "alternative_targets": [
            {"region_px": a[0], "region_source": a[1],
             "observation": a[2]}
            for a in alts
        ],
    }


def _leader_not_found():
    return {
        "state": "NOT_FOUND", "segments_px": [], "endpoint_px": None,
        "target_state": None, "target_region_id": None,
        "target_region_px": None, "target_observation": None,
        "alternative_target_regions_px": [], "alternative_targets": [],
    }


def _u(rows, balloons):
    return {
        "schema_version": "drawing_understanding.v1",
        "document_hash_sha256": SHA, "page": 1,
        "component_table": {
            "candidate": True, "rows": rows,
            "row_count": len(rows),
        },
        "balloon_candidates": balloons,
        "regions": [], "dimension_candidates": [],
        "identifier_candidates": [],
    }


def _cc(entry):
    return entry["component_consistency"]


# ---------- RQ-B3-04 — matriz categoria × forma observada -------------


def test_b3_cable_balloon_to_elongated_bar_compatible():
    """Cabo declarado + barra alongada saturada → COMPATIBLE_CANDIDATE
    (caso real: balão A→10420256 no 90261723)."""
    rows = [_row(0, "10420256", "A",
                 ["cabo", "pvc", "105°", "18awg", "vdar", "ul"])]
    bal = _balloon("A", _leader_single(obs=_obs(21.3, 0.91, hue=60)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    e = v["balloons"][0]
    cc = _cc(e)
    assert e["state"] == "BALLOON_LABEL_IDENTIFIED"
    assert cc["evaluated"] is True
    assert cc["state"] == "COMPATIBLE_CANDIDATE"
    ev = cc["evaluations"][0]
    assert ev["declared"]["category_class"] == "cable"
    assert ev["declared"]["color_tokens"] == ["VDAR"]
    assert ev["declared"]["description_source"] == (
        "row_cells_right_of_component_code")
    assert ev["observed"]["shape_class"] == "elongated_fill"
    # cor: preenchimento esquemático nunca vira cor de material
    assert ev["comparison"]["color"]["state"] == "NOT_COMPARABLE"


def test_b3_terminal_balloon_to_elongated_bar_conflict():
    """Terminal declarado + barra alongada → CONFLICT_CANDIDATE
    (cabo apontado por balão de terminal — exemplo negativo)."""
    rows = [_row(0, "10080110", "B",
                 ["term.", "olhal", "5,3", "0,5-1,5mm²"])]
    bal = _balloon("B", _leader_single(obs=_obs(21.3, 0.91, hue=60)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    cc = _cc(v["balloons"][0])
    assert cc["state"] == "CONFLICT_CANDIDATE"
    assert cc["evaluations"][0]["comparison"]["category"]["state"] == (
        "CONFLICT_CANDIDATE")


def test_b3_cable_balloon_to_compact_region_conflict():
    """Cabo declarado + região compacta → CONFLICT_CANDIDATE."""
    rows = [_row(0, "10380095", "A3",
                 ["cabo", "epr", "125/150°c", "22awg", "vm"])]
    bal = _balloon("A3", _leader_single(obs=_obs(1.4, 0.12, hue=0)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    cc = _cc(v["balloons"][0])
    assert cc["state"] == "CONFLICT_CANDIDATE"


def test_b3_terminal_to_compact_region_inconclusive():
    """Terminal declarado + região compacta → INCONCLUSIVE: a região é
    consistente mas não distingue terminal de luva/protetor."""
    rows = [_row(0, "10080106", "A4",
                 ["term.mag", "mate", "18-22awg", "ul"])]
    bal = _balloon("A4", _leader_single(obs=_obs(1.35, 0.12, hue=0)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    cc = _cc(v["balloons"][0])
    assert cc["state"] == "INCONCLUSIVE"
    assert "não distingue" in (
        cc["evaluations"][0]["comparison"]["category"]["reason"])


def test_b3_cable_to_mixed_region_inconclusive():
    """Cabo declarado + região composta (vista inteira com cabo e
    terminais) → INCONCLUSIVE — região não é corpo de cabo puro."""
    rows = [_row(0, "10380095", "A3", ["cabo", "epr", "22awg", "vm"])]
    bal = _balloon("A3", _leader_single(obs=_obs(4.2, 0.16, hue=0)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    assert _cc(v["balloons"][0])["state"] == "INCONCLUSIVE"


def test_b3_unknown_declared_category_inconclusive():
    """Descrição sem token de categoria → INCONCLUSIVE (não fabrica
    expectativa)."""
    rows = [_row(0, "99999999", "Z", ["xyz", "generico"])]
    bal = _balloon("Z", _leader_single(obs=_obs(21.0, 0.9, hue=60)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    assert _cc(v["balloons"][0])["state"] == "INCONCLUSIVE"


# ---------- RQ-B3-05 — ambiguidades preservadas ------------------------


def test_b3_ambiguous_regions_not_evaluated():
    """AMBIGUOUS_REGIONS → sem comparação; alternativas registradas com
    suas classes observadas, sem escolha silenciosa."""
    rows = [_row(0, "10080110", "B", ["term.", "olhal"])]
    alts = [
        ([0, 0, 400, 20], "rect", _obs(21.0, 0.91, hue=60)),
        ([0, 0, 30, 30], "rect", _obs(1.3, 0.12, hue=0)),
    ]
    bal = _balloon("B", _leader_ambiguous(alts))
    v = build_balloon_table_validation(_u(rows, [bal]))
    cc = _cc(v["balloons"][0])
    assert cc["state"] == "INCONCLUSIVE"
    assert cc["evaluated"] is False
    assert len(cc["alternatives"]) == 2
    assert {a["shape_class"] for a in cc["alternatives"]} == {
        "elongated_fill", "compact_or_outline"}


def test_b3_no_leader_not_evaluated():
    rows = [_row(0, "10420256", "A", ["cabo", "pvc", "18awg"])]
    bal = _balloon("A", _leader_not_found())
    v = build_balloon_table_validation(_u(rows, [bal]))
    cc = _cc(v["balloons"][0])
    assert cc["state"] == "INCONCLUSIVE"
    assert cc["evaluated"] is False


def test_b3_no_table_row_not_comparable():
    """Balão sem linha na tabela (caso real '1' do 90261723) →
    NOT_COMPARABLE, não conflito."""
    rows = [_row(0, "10420256", "A", ["cabo", "pvc", "18awg"])]
    bal = _balloon("1", _leader_single(obs=_obs(21.0, 0.9, hue=60)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    assert v["balloons"][0]["state"] == "NOT_LOCATED"
    assert _cc(v["balloons"][0])["state"] == "NOT_COMPARABLE"


def test_b3_ambiguous_table_rows_evaluated_each():
    """Duas linhas com mesmo rótulo → avaliação por linha, sem
    escolha silenciosa."""
    rows = [
        _row(0, "10380095", "A3", ["cabo", "epr", "vm"]),
        _row(1, "10380095", "A3", ["cabo", "epr", "vm"]),
    ]
    bal = _balloon("A3", _leader_single(obs=_obs(21.0, 0.9, hue=60)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    e = v["balloons"][0]
    cc = _cc(e)
    assert e["state"] == "AMBIGUOUS"
    assert len(cc["evaluations"]) == 2
    assert {ev["row_index"] for ev in cc["evaluations"]} == {0, 1}
    # linhas idênticas → mesmo estado consolidado
    assert cc["state"] == "COMPATIBLE_CANDIDATE"


def test_b3_repeated_label_occurrences_independent():
    """Duas ocorrências A3 com destinos distintos → cada uma avaliada
    pela própria região (sem mistura por rótulo)."""
    rows = [_row(0, "10380095", "A3", ["cabo", "epr", "vm"])]
    b1 = _balloon("A3", _leader_single(
        obs=_obs(21.0, 0.9, hue=60), region_id="uleadtgt:0"))
    b2 = _balloon("A3", _leader_single(
        obs=_obs(1.2, 0.1, hue=0), region_id="uleadtgt:1"))
    v = build_balloon_table_validation(_u(rows, [b1, b2]))
    states = [_cc(e)["state"] for e in v["balloons"]]
    # ambas AMBIGUOUS na tabela (mesmo rótulo), mas as coerências
    # visuais são por ocorrência: cabo→barra COMPATIBLE, cabo→compacta
    # CONFLICT — avaliadas independentemente
    assert states == ["COMPATIBLE_CANDIDATE", "CONFLICT_CANDIDATE"]


# ---------- RQ-B3-03 — cor só quando tecnicamente aplicável ------------


def test_b3_color_not_comparable_schematic_fill():
    """Cabo VDAR declarado + região azul → NOT_COMPARABLE: o azul do
    desenho é esquemático, não cor de material (caso real 90261723)."""
    rows = [_row(0, "10420256", "A", ["cabo", "pvc", "18awg", "vdar"])]
    bal = _balloon("A", _leader_single(obs=_obs(21.0, 0.9, hue=60)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    ev = _cc(v["balloons"][0])["evaluations"][0]
    assert ev["comparison"]["color"]["state"] == "NOT_COMPARABLE"
    # mas a observação do matiz fica registrada como evidência
    assert ev["observed"]["dominant_hue"] == 60


def test_b3_color_material_semantics_conflict():
    """Caminho material (sintético): VM declarado + matiz azul →
    CONFLICT_CANDIDATE."""
    rows = [_row(0, "10380095", "A3", ["cabo", "epr", "vm"])]
    bal = _balloon("A3", _leader_single(
        obs=_obs(21.0, 0.9, hue=60, frac=0.9, semantics="material")))
    v = build_balloon_table_validation(_u(rows, [bal]))
    cc = _cc(v["balloons"][0])
    assert cc["state"] == "CONFLICT_CANDIDATE"
    assert cc["evaluations"][0]["comparison"]["color"]["state"] == (
        "CONFLICT_CANDIDATE")


def test_b3_color_material_semantics_compatible():
    rows = [_row(0, "10380095", "A3", ["cabo", "epr", "vm"])]
    bal = _balloon("A3", _leader_single(
        obs=_obs(21.0, 0.9, hue=5, frac=0.9, semantics="material")))
    v = build_balloon_table_validation(_u(rows, [bal]))
    assert _cc(v["balloons"][0])["state"] == "COMPATIBLE_CANDIDATE"


def test_b3_color_no_declared_not_comparable():
    rows = [_row(0, "10420256", "A", ["cabo", "pvc", "18awg"])]
    bal = _balloon("A", _leader_single(
        obs=_obs(21.0, 0.9, hue=60, frac=0.9, semantics="material")))
    v = build_balloon_table_validation(_u(rows, [bal]))
    assert _cc(v["balloons"][0])["evaluations"][0]["comparison"][
        "color"]["state"] == "NOT_COMPARABLE"


# ---------- casos de erro e abstenção ----------------------------------


def test_b3_monochrome_no_observation_inconclusive():
    """Desenho monocromático/sem medida de cor → shape unknown →
    INCONCLUSIVE (nunca falso conflito por ausência de dado)."""
    rows = [_row(0, "10080110", "B", ["term.", "olhal"])]
    bal = _balloon("B", _leader_single(obs=None))
    v = build_balloon_table_validation(_u(rows, [bal]))
    cc = _cc(v["balloons"][0])
    assert cc["state"] == "INCONCLUSIVE"
    assert cc["evaluations"][0]["observed"]["shape_class"] == "unknown"


def test_b3_typed_description_fallback():
    """Linha sem cells → descrição declarada via campo tipado."""
    rows = [{
        "row": 0, "page": 1,
        "fields": {
            "component_code": {"normalized_value": "10420256"},
            "description": {"raw_text": "CABO PVC 105 18AWG VDAR"},
        },
        "association_status": "FIELD_IDENTIFIED", "cells": [],
    }]
    rows[0]["fields"]["item"] = {"normalized_value": "A"}
    bal = _balloon("A", _leader_single(obs=_obs(21.0, 0.9, hue=60)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    ev = _cc(v["balloons"][0])["evaluations"][0]
    assert ev["declared"]["category_class"] == "cable"
    assert ev["declared"]["description_source"] == (
        "typed_description_field")
    assert ev["declared"]["color_tokens"] == ["VDAR"]


def test_b3_norm_eval_recorded_not_extended():
    """Grupo sem norma ratificada (1038/1042) → norm_status registrado
    como bloqueio/não aplicável, categoria segue pelo token declarado."""
    rows = [_row(0, "10380095", "A3", ["cabo", "epr", "22awg", "vm"])]
    bal = _balloon("A3", _leader_single(obs=_obs(21.0, 0.9, hue=60)))
    v = build_balloon_table_validation(_u(rows, [bal]))
    ev = _cc(v["balloons"][0])["evaluations"][0]
    assert ev["declared"]["norm_status"] == "OWNER_BLOCKED"
    assert ev["declared"]["category_class"] == "cable"


def test_b3_summary_counts():
    rows = [
        _row(0, "10420256", "A", ["cabo", "pvc", "vdar"]),
        _row(1, "10080110", "B", ["term.", "olhal"]),
    ]
    bals = [
        _balloon("A", _leader_single(obs=_obs(21.0, 0.9, hue=60))),
        _balloon("B", _leader_single(obs=_obs(1.3, 0.1, hue=0))),
    ]
    v = build_balloon_table_validation(_u(rows, bals))
    s = v["component_consistency_summary"]
    assert s["compatible_candidates"] == 1
    assert s["conflict_candidates"] == 0
    assert s["inconclusive"] == 1
