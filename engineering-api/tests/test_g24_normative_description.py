"""G24 — normative PI/MP description evaluation (RQ24-01..09)."""
from engineering_app.application.drawing.normative_description import (
    NORM_REFS, evaluate_description, evaluate_pi_mp_coherence,
    resolve_applicability,
)


def ev(code, ptype, desc, source="TOTVS"):
    return evaluate_description(
        product_code=code, product_type=ptype,
        description_raw=desc, description_source=source)


# ---- PI 50xx (norm: codigos-intermediarios-pi.md) ----
def test_pi_canonical_pass():
    r = ev("50233507", "PI", "CA18MARR-00152/10/06-0000-0110")
    assert r["overall_status"] == "PASS"
    assert r["applied_ruleset"]["sha256"] == NORM_REFS["PI_50XX"]["sha256"]
    names = {a["name"] for a in r["extracted_attributes"]}
    assert {"isolation_prefix", "gauge", "color", "length_mm",
            "decape_left_mm", "decape_right_mm", "terminal_left",
            "isolator_left"} <= names


def test_pi_cb_material():
    r = ev("50213207", "PI", "CB18VERD-00512/10/10-0000-0000")
    iso = next(a for a in r["extracted_attributes"]
               if a["name"] == "isolation_prefix")
    assert iso["normalized_value"] == "CB"
    assert r["rule_results"][0]["reason"] == "material: EPR"


def test_pi_mabr_color_owner_blocked():
    r = ev("50210001", "PI", "CA18MABR-00100/05/05-0000-0000")
    color_rule = next(x for x in r["rule_results"]
                      if x["rule_id"] == "PI50-COLOR-01")
    assert color_rule["status"] == "OWNER_BLOCKED"
    assert r["overall_status"] == "OWNER_BLOCKED"


def test_pi_unparseable_inconclusive_not_fail():
    r = ev("50213206", "PI", "texto truncado OCR parcial")
    assert r["overall_status"] == "INCONCLUSIVE"
    assert r["rule_results"][0]["status"] == "INCONCLUSIVE"


def test_pi_absent_desc_no_fabrication():
    r = ev("50213206", "PI", None)
    assert r["overall_status"] == "INCONCLUSIVE"
    assert "no field is fabricated" in r["unknowns"][0]


def test_pi_drawing_source_separate():
    r = ev("50213206", "PI", "CA18BRAN-00512/10/10-0000-0000",
           source="DRAWING")
    assert r["description_source"] == "DRAWING"
    assert r["no_business_write"] is True


# ---- MP cables 1001-1005 ----
def test_cable_1001_pass():
    r = ev("10010001", "MP",
           "CABO PVC 70°C 0,75MM2 PT 450/750V BWF ESTANHADO NBR")
    assert r["overall_status"] == "PASS"
    attrs = {a["name"]: a["normalized_value"]
             for a in r["extracted_attributes"]}
    assert attrs["material"] == "PVC"
    assert attrs["color"] == "PT"


def test_cable_missing_fields_inconclusive_not_fail():
    r = ev("10020002", "MP", "CABO")
    assert r["overall_status"] == "INCONCLUSIVE"


def test_cable_wrong_prefix_violation_candidate():
    r = ev("10030003", "MP",
           "FIO PVC 105°C 0,5MM2 VM 300V")
    prefix = next(x for x in r["rule_results"]
                  if x["rule_id"] == "MP-CABO-PREFIX")
    assert prefix["status"] == "VIOLATION_CANDIDATE"


# ---- MP 1038: norm extension NOT ratified (D1) ----
def test_cable_1038_owner_blocked_no_extrapolation():
    r = ev("10380040", "MP", "CABO EPR 125/150°C 18AWG BN 600V UL")
    assert r["overall_status"] == "OWNER_BLOCKED"
    assert r["applied_ruleset"] is None
    assert "D1" in r["unknowns"][0]


# ---- MP 1008 terminals ----
def test_terminal_1008_canonical():
    r = ev("10080136", "MP",
           "TERM. BANDEIRA 6,30X0,80 0,50-1,50MM2 ESTANHADO "
           "C/ISOLACAO GRANEL 90° ROHS")
    assert r["overall_status"] == "PASS"


def test_terminal_mm_not_silently_mm2():
    r = ev("10080136", "MP",
           "TERM. BANDEIRA 6,3X0,8 1,0-2,6MM UL ESTANHADO")
    rng = next(x for x in r["rule_results"]
               if x["rule_id"] == "MP-1008-RANGE")
    assert rng["status"] == "WARNING"
    assert "MM" in (rng["reason"] or "")
    # MM nunca vira MM2 na normalização
    attr = next(a for a in r["extracted_attributes"]
                if a["name"] == "gauge_range")
    assert "MM2" not in attr["normalized_value"]


# ---- MP 1009 isolators ----
def test_isolator_1009_canonical():
    r = ev("10090010", "MP", "ISOLADOR NYLON RETO 6,3 PT UL94 V2")
    assert r["overall_status"] == "PASS"


def test_isolator_90_orient():
    r = ev("10090020", "MP", "ISOLADOR NYLON 90° 4,8 AL ROHS")
    o = next(a for a in r["extracted_attributes"]
             if a["name"] == "orientation")
    assert o["normalized_value"] == "90"


def test_isolator_alias_not_equated():
    r = ev("10090010", "MP", "ISOLADOR NYLON RETO 6,3 PRETA UL94 V2")
    color = next(x for x in r["rule_results"]
                 if x["rule_id"] == "MP-1009-COLOR")
    # PRETA não é abreviação PT — ausência vira INCONCLUSIVE,
    # equivalência lexical nunca presume alias aprovado
    assert color["status"] == "INCONCLUSIVE"


# ---- Applicability fail-closed ----
def test_unknown_group_not_applicable():
    r = ev("99990001", "MP", "QUALQUER COISA")
    assert r["overall_status"] == "NOT_APPLICABLE"


def test_blank_code_not_applicable():
    r = ev("", "MP", "CABO PVC")
    assert r["overall_status"] == "NOT_APPLICABLE"


def test_unknown_source_owner_blocked():
    r = ev("50213206", "PI", "CA18BRAN-00512/10/10-0000-0000",
           source="MYSTERY")
    assert r["overall_status"] == "OWNER_BLOCKED"


# ---- PI x BOM coherence ----
def test_coherence_pvc_vs_epr_conflict_candidate():
    c = evaluate_pi_mp_coherence(
        pi_description="CA18BRAN-00512/10/10-0000-0000",
        mp_descriptions=["CABO EPR 125/150°C 18AWG BN 600V"])
    iso = next(x for x in c["checks"]
               if x["rule_id"] == "COH-ISO-MATERIAL")
    assert iso["status"] == "VIOLATION_CANDIDATE"
    assert iso["observed"]["pi"] == "PVC"
    assert "EPR" in iso["observed"]["mp"]


def test_coherence_matching_material_pass():
    c = evaluate_pi_mp_coherence(
        pi_description="CB18VERD-00512/10/10-0000-0000",
        mp_descriptions=["CABO EPR 18AWG VD 600V"])
    assert next(x for x in c["checks"]
                if x["rule_id"] == "COH-ISO-MATERIAL")["status"] == "PASS"
    assert next(x for x in c["checks"]
                if x["rule_id"] == "COH-GAUGE")["status"] == "PASS"


def test_coherence_no_mp_material_inconclusive():
    c = evaluate_pi_mp_coherence(
        pi_description="CA18BRAN-00512/10/10-0000-0000",
        mp_descriptions=["TERM. BANDEIRA 6,3X0,8 ESTANHADO"])
    assert next(x for x in c["checks"]
                if x["rule_id"] == "COH-ISO-MATERIAL"
                )["status"] == "INCONCLUSIVE"


def test_coherence_position_never_inferred():
    c = evaluate_pi_mp_coherence(
        pi_description="CA18BRAN-00512/10/10-0000-0000",
        mp_descriptions=["CABO PVC 18AWG BR 600V"])
    pos = next(x for x in c["checks"]
               if x["rule_id"] == "COH-TERM-POSITION")
    assert pos["status"] == "NOT_APPLICABLE"


def test_coherence_unparseable_pi_inconclusive():
    c = evaluate_pi_mp_coherence(
        pi_description="lixo de OCR", mp_descriptions=["CABO PVC"])
    assert c["status"] == "INCONCLUSIVE"


# ---- Contract shape / provenance ----
def test_contract_shape_and_ruleset_version():
    r = ev("10090010", "MP", "ISOLADOR NYLON RETO 6,3 PT UL94 V2")
    assert r["contract_version"] == "normative_description.v1"
    assert r["applied_ruleset"]["owner"] == "ENGENHARIA"
    assert r["review_status"].startswith("DRAFT/CANDIDATE")
    assert r["engine"]["ai_used"] is False
    for rule in r["rule_results"]:
        assert set(rule) >= {"rule_id", "requirement", "applicable",
                             "status", "observed", "expected"}
    for attr in r["extracted_attributes"]:
        assert set(attr) >= {"name", "raw_span", "normalized_value",
                             "extraction_method", "state"}


def test_applicability_resolver_matrix():
    assert resolve_applicability("50213206", "PI")[0] == "PI_50XX"
    assert resolve_applicability("10049999", "MP")[0] == "MP_CABLES_1001_1005"
    assert resolve_applicability("10080001", "MP")[0] == "MP_TERMINAL_1008"
    assert resolve_applicability("10090001", "MP")[0] == "MP_ISOLATOR_1009"
    assert resolve_applicability("10380040", "MP")[2] is not None  # blocked
    assert resolve_applicability("77770001", "MP")[0] is None


# ---- Integração: bloco normativo aditivo nos records do comparador ----
from engineering_app.application.drawing.bom_structure_comparator import (
    compare_bom_to_drawing,
)


def _t(rows):
    return {"candidate": True, "rows": rows, "row_count": len(rows),
            "code_count": sum(1 for r in rows if r.get("component_code")),
            "unreliable_boundary": False}


def _grp_row(parent, code, y, desc, pi_desc):
    return {
        "row": y, "y_px": float(y),
        "component_code": parent, "description": desc,
        "quantity": "1", "parent_group_description": pi_desc,
        "cells": [
            {"text": parent, "col": 0, "row": y,
             "col_type": "component_code",
             "bounding_box_px": [10, y, 60, y + 8], "page": 1},
            {"text": code, "col": 1, "row": y,
             "bounding_box_px": [120, y, 180, y + 8], "page": 1},
        ],
    }


def _occ(oid, code, parent, depth, desc, ptype=None):
    return {
        "occurrence_id": oid, "component_code": code,
        "component_type": ptype or ("PI" if code.startswith("5") else "MP"),
        "component_description": desc,
        "parent_code": parent, "depth": depth,
        "path": f"X/{code}" if depth == 1 else code,
        "quantity_raw": 1, "unit_raw": "PC",
    }


def test_comparator_records_carry_normative_blocks():
    """DRAWING e TOTVS avaliados separadamente + coerência PI×MP."""
    pi_d = "CA18MARR-00152/10/06-0000-0110"
    mp_d = "TERM. BANDEIRA 6,30X0,80 0,50-1,50MM2 ESTANHADO C/ISOLACAO GRANEL"
    table = _t([
        _grp_row("50233507", "10080136", 10, mp_d, pi_d),
    ])
    bom = [
        _occ("O1", "50233507", "90263680", 1, pi_d),
        _occ("O2", "10080136", "50233507", 2, mp_d),
    ]
    out = compare_bom_to_drawing(
        product_code="90263680", bom_occurrences=bom,
        component_table=table, tokens=None)
    report = out["validation_report"]
    recs = {r["component_code"]: r for r in report["occurrence_records"]}
    mp = recs["10080136"]
    assert mp["normative"] is not None
    assert mp["normative"]["totvs_description_normative"][
        "overall_status"] == "PASS"
    assert mp["normative"]["drawing_description_normative"][
        "description_source"] == "DRAWING"
    assert "pi_bom_coherence" in mp["normative"]
    # findings continuam candidatos — nada vira NC
    assert report["automatic_nc"] is False
    assert report["engineering_approval"] == "NOT_APPROVED"


def test_comparator_1038_stays_owner_blocked_in_report():
    table = _t([
        _grp_row("50213206", "10380040", 10,
                 "CABO EPR 125/150°C 18AWG BN 600V",
                 "CA18BRAN-00512/10/10-0000-0000"),
    ])
    bom = [
        _occ("O1", "50213206", "90263680", 1,
             "CA18BRAN-00512/10/10-0000-0000"),
        _occ("O2", "10380040", "50213206", 2,
             "CABO EPR 125/150°C 18AWG BN 600V"),
    ]
    out = compare_bom_to_drawing(
        product_code="90263680", bom_occurrences=bom,
        component_table=table, tokens=None)
    recs = {r["component_code"]: r
            for r in out["validation_report"]["occurrence_records"]}
    assert recs["10380040"]["normative"][
        "totvs_description_normative"]["overall_status"] == "OWNER_BLOCKED"
