"""R12 — investigação guiada pela estrutura oficial (I-01..I-05)."""
from __future__ import annotations

from engineering_app.application.drawing.drawing_investigation import (
    INVESTIGATION_SCHEMA,
    execute_investigations,
    plan_investigations,
)
from engineering_app.application.drawing.object_profiles_builder import (
    build_object_profiles,
)

_SHA = "sha-pdf"
_SRC = "api-delpi:/products/P/structure"

_BOM = [
    {"occurrence_id": "O0001", "component_code": "50226113",
     "parent_code": "P", "depth": 1, "path": "50226113",
     "quantity_raw": "1", "unit_raw": "PC", "component_type": "PI"},
    {"occurrence_id": "O0002", "component_code": "10020033",
     "parent_code": "50226113", "depth": 2, "path": "50226113/10020033",
     "quantity_raw": "643", "unit_raw": "MT", "component_type": "MP"},
    {"occurrence_id": "O0003", "component_code": "10020033",
     "parent_code": "50226114", "depth": 2, "path": "50226114/10020033",
     "quantity_raw": "643", "unit_raw": "MT", "component_type": "MP"},
]


def _fld(text, box=None):
    return {"raw_text": text, "normalized_value": text,
            "bounding_box_px": box or [1, 1, 9, 1, 9, 9, 1, 9],
            "col": 0, "association_state": "FIELD_IDENTIFIED"}


def _row(i, code, qty="1", item="A1", desc="X", ambiguous=False):
    cells = [
        {"text": code, "col": 2, "row": i, "col_type": "component_code",
         "bounding_box_px": [1, 1, 9, 1, 9, 9, 1, 9]},
    ]
    if ambiguous:
        cells[0]["ambiguous"] = True
    return {"row": i, "y_px": 100 + i * 10, "cells": cells, "col_count": 4,
            "fields": {"component_code": _fld(code), "quantity": _fld(qty),
                       "item": _fld(item), "description": _fld(desc)},
            "item": item, "quantity": qty, "component_code": code,
            "description": desc, "association_status": "FIELD_IDENTIFIED"}


def _u(rows=(), idents=(), sha=_SHA):
    return {"schema_version": "drawing_understanding.v1",
            "document_hash_sha256": sha, "page": 1,
            "component_table": {"rows": list(rows)},
            "identifier_candidates": list(idents),
            "dimension_candidates": [], "regions": []}


def _ident(text, region):
    return {"text": text, "kind": "identifier_candidate", "region": region,
            "bounding_box_px": [1, 1, 9, 1, 9, 9, 1, 9]}


def _build(rows=(), idents=(), sha=_SHA, bom=_BOM):
    return build_object_profiles(
        bom_occurrences=bom, visual_observations=[],
        understanding=_u(rows, idents, sha),
        document_sha=_SHA, official_source_ref=_SRC,
        include_investigations=True,
    )


# ---------- planejamento -------------------------------------------------


def test_plan_per_occurrence_typed():
    out = _build()
    gi = out["guided_investigations"]
    assert gi["schema_version"] == INVESTIGATION_SCHEMA
    plan = gi["plan"]
    assert len(plan) == 3
    assert plan[0]["expected_object_id"] == "O0001"
    assert plan[0]["attribute"] == "component_code"
    assert plan[0]["expected_source"] == _SRC
    assert plan[0]["state"] == "NOT_CHECKED"


def test_repeated_code_keeps_distinct_identities():
    out = _build()
    ids = [p["expected_object_id"] for p in
           out["guided_investigations"]["plan"]]
    assert ids == ["O0001", "O0002", "O0003"]


def test_component_type_does_not_change_mechanism():
    out = _build()
    assert all(p["search_strategy"] == "EXACT_THEN_CONTEXTUAL"
               for p in out["guided_investigations"]["plan"])


# ---------- matching ------------------------------------------------------


def test_exact_code_in_valid_row_match_candidate():
    out = _build(rows=[_row(0, "10020033")])
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    c = res["O0002"]["investigations"][0]
    assert c["state"] == "MATCH_CANDIDATE"
    assert c["evidence_refs"]
    assert res["O0002"]["overall_state"] == "MATCH_CANDIDATE"


def test_code_only_in_title_block_not_component():
    out = _build(idents=[_ident("10020033", "title_block")])
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    c = res["O0002"]["investigations"][0]
    assert c["state"] == "AMBIGUOUS"
    assert "não-componente" in c["uncertainty_reason"]


def test_similar_but_different_code_ambiguous_not_match():
    out = _build(rows=[_row(0, "10020039")])
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    c = res["O0001"]["investigations"][0]
    assert c["state"] == "NOT_LOCATED"  # 50226113 ausente
    out2 = _build(rows=[_row(0, "10020039")],
                  idents=[_ident("10020034", "drawing_area")])
    c2 = {r["occurrence_id"]: r for r in
          out2["guided_investigations"]["occurrence_results"]}[
        "O0002"]["investigations"][0]
    assert c2["state"] == "AMBIGUOUS"
    assert c2["observed_value"] is None or c2["state"] != "MATCH_CANDIDATE"


def test_non_numeric_quantity_ambiguous():
    out = _build(rows=[_row(0, "10020033", qty="1/2")])
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    qty = res["O0002"]["investigations"][1]
    assert qty["state"] == "AMBIGUOUS"
    assert qty["observed"]["assembly_quantity"] is None
    assert qty["observed"]["assembly_quantity_raw"] == "1/2"


def test_expected_component_not_located_inconclusive():
    out = _build()
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    assert res["O0001"]["overall_state"] == "EXPECTED_COMPONENT_NOT_LOCATED"
    s = out["guided_investigations"]["summary"]
    assert s["not_located"] == 3


def test_unmatched_drawing_candidate_not_bom_error():
    out = _build(rows=[_row(0, "99999999")])
    un = out["guided_investigations"]["unmatched_drawing_candidates"]
    assert len(un) == 1
    assert un[0]["state"] == "UNMATCHED_DRAWING_CANDIDATE"
    assert "não é prova" in un[0]["reason"]


def test_repeated_code_both_occurrences_get_relations():
    out = _build(rows=[_row(0, "10020033")])
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    for oid in ("O0002", "O0003"):
        rel = res[oid]["investigations"][2]
        assert rel["state"] == "MATCH_CANDIDATE"
        assert rel["relation_count"] == 1
        assert "arbitrariamente" in rel["uncertainty_reason"]


def test_two_rows_same_code_ambiguous():
    out = _build(rows=[_row(0, "10020033"), _row(1, "10020033")])
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    c = res["O0002"]["investigations"][0]
    assert c["state"] == "AMBIGUOUS"
    assert len(c["candidate_rows"]) == 2


# ---------- provenance / segurança ---------------------------------------


def test_incompatible_document_sha_fail_closed():
    out = _build(rows=[_row(0, "10020033")], sha="sha-other")
    gi = out["guided_investigations"]
    assert gi["document_identity"]["match"] is False
    assert all(
        c["state"] == "NOT_COMPARABLE"
        for r in gi["occurrence_results"]
        for c in r["investigations"]
    )


def test_no_understanding_not_checked():
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=None, document_sha=_SHA,
        official_source_ref=_SRC, include_investigations=True,
    )
    res = out["guided_investigations"]["occurrence_results"]
    assert res[0]["investigations"][0]["state"] == "NOT_LOCATED"


def test_quantity_semantics_context_preserved():
    out = _build()
    ctx = out["guided_investigations"]["plan"][1]["context"]
    assert ctx["consumption_quantity"] == "643"
    assert ctx["consumption_unit"] == "MT"


def test_report_section_versioned_additive():
    out = _build()
    gi = out["guided_investigations"]
    assert gi["not_official"] is True
    assert gi["state"] == "DRAFT/CANDIDATE"
    assert gi["human_review_required"] is True
    assert gi["summary"]["expected_occurrences"] == 3


def test_domain_module_still_pure():
    import inspect
    import engineering_app.application.drawing.drawing_investigation as m
    src = inspect.getsource(m)
    for bad in ("cv2", "paddle", "requests", "httpx", "sqlalchemy",
                "fastapi"):
        assert bad not in src


# ---------- R12.1 — fonte oficial ausente / indisponível ------------------


def test_no_bom_no_unmatched_fail_closed():
    """R12.1-A: sem estrutura oficial, zero unmatched e cobertura nula."""
    out = build_object_profiles(
        bom_occurrences=[], visual_observations=[],
        understanding=_u(rows=[_row(0, "99999999")],
                         idents=[_ident("12345678", "drawing_area")]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="NOT_PROVIDED",
        include_investigations=True,
    )
    gi = out["guided_investigations"]
    assert gi["official_source_state"] == "NOT_PROVIDED"
    assert gi["unmatched_drawing_candidates"] == []
    assert gi["occurrence_results"] == []
    s = gi["summary"]
    assert s["expected_occurrences"] == 0
    assert s["investigations_executed"] == 0
    assert s["effective_coverage"] is None
    assert any(
        "OFFICIAL_COMPARISON_NOT_EXECUTED" in lim
        for lim in gi["limitations"]
    )
    # observações visuais preservadas como objetos candidatos
    assert out["objects_by_type"].get("drawing_table_item") == 1


def test_unavailable_source_never_empty_bom():
    """Indisponibilidade ≠ BOM vazia: estado explícito, sem reconciliação."""
    out = build_object_profiles(
        bom_occurrences=[], visual_observations=[],
        understanding=_u(rows=[_row(0, "99999999")]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="UNAVAILABLE",
        include_investigations=True,
    )
    gi = out["guided_investigations"]
    assert gi["official_source_state"] == "UNAVAILABLE"
    assert gi["unmatched_drawing_candidates"] == []


# ---------- R13 — investigação progressiva + correções --------------------


def test_root_product_identifier_not_component_r13_01():
    """90264302 no desenho ≠ componente extra — tipo próprio."""
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=_u(idents=[_ident("90264302", "drawing_area"),
                                 _ident("99999999", "drawing_area")]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        include_investigations=True,
    )
    gi = out["guided_investigations"]
    roots = [x["observed_raw_value"] for x in
             gi["root_product_identifiers"]]
    assert "90264302" in roots
    un = [x["observed_raw_value"] for x in
          gi["unmatched_drawing_candidates"]]
    assert "90264302" not in un and "99999999" in un


def test_relation_carries_spatial_evidence_r13_02():
    """REPRESENTED_BY preserva página/bbox da observação, não só o código."""
    out = _build(rows=[_row(0, "10020033")])
    rel = [r for r in out["relations"]
           if r["relation_type"] == "REPRESENTED_BY"][0]
    kinds = {e["source_kind"] for e in rel["evidence_refs"]}
    assert "code_match" in kinds
    assert any(
        e.get("bounding_box") or e.get("coordinate_system")
        for e in rel["evidence_refs"]
    )


def test_progressive_contextual_search_recovers_raw_cell_code():
    """Código exato em célula bruta de linha ambígua → contextual search."""
    row = _row(0, "10020033")
    row["fields"] = {}  # associação perdida — linha ambígua
    row["association_status"] = "UNRESOLVED"
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=_u(rows=[row]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        progressive={"budget": {"max_crops": 2}},
        include_investigations=True,
    )
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    hist = res["O0002"].get("search_history") or []
    stages = [h["stage"] for h in hist]
    assert "EXISTING_EVIDENCE" in stages and "CONTEXTUAL_SEARCH" in stages
    ctx = hist[1]
    assert ctx["result"] == "ROW_ASSOCIATION_CANDIDATE"


def test_progressive_recheck_capability_unavailable_honest():
    """Sem ports/pdf, recorte responde CAPABILITY_UNAVAILABLE — não inventa."""
    row = _row(0, "10020033")
    row["fields"] = {}
    row["association_status"] = "UNRESOLVED"
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=_u(rows=[row]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        progressive={"budget": {"max_crops": 2}},
        include_investigations=True,
    )
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    recheck = [h for h in res["O0002"].get("search_history", [])
               if h["stage"] == "TARGETED_RECHECK"][0]
    assert recheck["result"] == "CAPABILITY_UNAVAILABLE"


def test_balloons_never_fabricated_without_primitives():
    out = _build(rows=[_row(0, "10020033")])
    out2 = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=_u(rows=[_row(0, "10020033")]),
        document_sha=_SHA, official_source_ref=_SRC,
        product_code="90264302", progressive={"budget": {}},
        include_investigations=True,
    )
    assert out2["guided_investigations"]["balloon_candidates"] == []


def test_empty_confirmed_bom_reconciles():
    """BOM oficialmente vazia pode reconciliar: todo visual é unmatched."""
    out = build_object_profiles(
        bom_occurrences=[], visual_observations=[],
        understanding=_u(rows=[_row(0, "99999999")]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="EMPTY_CONFIRMED",
        include_investigations=True,
    )
    gi = out["guided_investigations"]
    assert gi["official_source_state"] == "EMPTY_CONFIRMED"
    un = gi["unmatched_drawing_candidates"]
    assert len(un) == 1
    assert un[0]["observed_raw_value"] == "99999999"
