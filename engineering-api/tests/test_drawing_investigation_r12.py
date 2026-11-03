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


class _FakeRenderer:
    def render_region(self, pdf, *, page, region_px, reference_dpi,
                      dpi, margin_px):
        class _R:
            image_bytes = b"png"
            width, height, dpi, page = 40, 20, 300, 1
            offset_px = (0.0, 0.0)
        return _R()


class _FakeOcr:
    def __init__(self, tokens):
        self._tokens = tokens

    def extract_text(self, image):
        class _T:
            def __init__(self, text):
                self.text = text
        class _Res:
            def __init__(self, toks):
                self.tokens = toks
        return _Res([_T(t) for t in self._tokens])


def test_targeted_recheck_with_real_ports_contract():
    """R13 closure: ports disponíveis → recorte executa de verdade."""
    row = _row(0, "10020033")
    row["fields"] = {}
    row["association_status"] = "UNRESOLVED"
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=_u(rows=[row]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        progressive={
            "budget": {"max_crops": 4, "max_dpi": 300,
                       "max_pixels": 4_000_000},
            "pdf_bytes": b"%PDF-fake",
            "renderer": _FakeRenderer(),
            "ocr": _FakeOcr(["10020033", "CABO"]),
            "page": 1, "reference_dpi": 200,
        },
        include_investigations=True,
    )
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    hist = res["O0002"]["search_history"]
    recheck = [h for h in hist if h["stage"] == "TARGETED_RECHECK"][0]
    assert recheck["result"] == "CODE_OBSERVED"
    assert recheck["observations"][0]["method"] == "localized_ocr_recheck"
    assert res["O0002"]["overall_state"] == "MATCH_CANDIDATE"


def test_recheck_budget_exhaustion_inconclusive():
    row = _row(0, "10020033")
    row["fields"] = {}
    row["association_status"] = "UNRESOLVED"
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=_u(rows=[row]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        progressive={
            "budget": {"max_crops": 0},
            "pdf_bytes": b"%PDF-fake",
            "renderer": _FakeRenderer(),
            "ocr": _FakeOcr(["10020033"]),
            "page": 1,
        },
        include_investigations=True,
    )
    res = {r["occurrence_id"]: r for r in
           out["guided_investigations"]["occurrence_results"]}
    recheck = [h for h in res["O0002"]["search_history"]
               if h["stage"] == "TARGETED_RECHECK"][0]
    assert recheck["result"] == "RESOURCE_LIMIT_REACHED"
    assert res["O0002"]["overall_state"] != "MATCH_CANDIDATE"


def test_balloon_detected_promotes_to_object_with_evidence():
    """Primitiva circular + token contido → BALLOON objeto + relações."""
    u = _u(rows=[_row(0, "10020033", item="7")])
    u["graphic_primitives"] = [
        {"type": "circle",
         "bounding_box_px": [40, 50, 70, 50, 70, 80, 40, 80]},
    ]
    u["_tokens"] = [
        {"normalized_text": "7", "region": "drawing_area",
         "bounding_box_px": [50, 58, 60, 58, 60, 70, 50, 70]},
    ]
    u["geometry_regions"] = [
        {"id": "g1", "type": "geometry", "box_px": [0, 0, 400, 400]},
    ]
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u,
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        include_investigations=True,
    )
    types = out["objects_by_type"]
    assert types.get("balloon") == 1
    rel_types = out["relations_by_type"]
    assert rel_types.get("REFERENCED_BY") == 1   # item 7 → balão
    assert rel_types.get("POINTS_TO") == 1       # balão → geometria (containment)
    gi = out["guided_investigations"]
    assert gi["balloon_candidates"][0]["item_label"] == "7"
    assert gi["balloon_candidates"][0]["identification_method"] == \
        "primitive_containment"


def test_consolidated_summary_states():
    out = _build(rows=[_row(0, "10020033")])
    s = out["guided_investigations"]["summary"]
    assert "checks_by_state" in s
    assert s["checks_by_state"].get("MATCH_CANDIDATE", 0) >= 1
    assert s["global_state"] in {"MATCH_CANDIDATE", "INCONCLUSIVE"}
    assert "global_state" != "PASS"


# ---------- M4 — governed official cross-check ---------------------------


def test_m4_contract_matrix_present():
    out = _build()
    cm = out["guided_investigations"]["official_cross_check"][
        "contract_matrix"]
    assert any(s["name"] == "product.structure" for s in cm["sources"])
    rules = {r["rule"] for r in cm["comparability_rules"]}
    assert any("NOT_COMPARABLE" in r for r in rules)


def test_m4_multiplicity_many_to_one_preserved():
    """2 ocorrências + 1 linha do mesmo código → MANY_TO_ONE, não colapsa."""
    out = _build(rows=[_row(0, "10020033")])
    m = out["guided_investigations"]["official_cross_check"][
        "multiplicity_analysis"]["10020033"]
    assert m["bom_occurrence_ids"] == ["O0002", "O0003"]
    assert m["drawing_item_ids"] == ["urow:0"]
    assert m["pairing"] == "MANY_TO_ONE"


def test_m4_component_code_match_only_exact():
    out = _build(rows=[_row(0, "10020033")])
    vs = {v["expected_object_id"]: v for v in
          out["guided_investigations"]["official_cross_check"][
              "attribute_verifications"]
          if v["attribute"] == "component_code"}
    assert vs["O0002"]["state"] == "MATCH"
    assert vs["O0002"]["observed_value"] == "10020033"
    assert vs["O0001"]["state"] == "UNKNOWN"  # ausência ≠ divergência


def test_m4_quantities_never_comparable():
    """500mm consumo × 1 montagem → NOT_COMPARABLE por atributo."""
    out = _build(rows=[_row(0, "10020033")])
    vs = [v for v in
          out["guided_investigations"]["official_cross_check"][
              "attribute_verifications"]
          if v["attribute"] == "assembly_quantity"]
    assert all(v["state"] == "NOT_COMPARABLE" for v in vs)


def test_m4_revision_domains_not_comparable():
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=dict(_u(), revision_candidates=[{"revision": "02"}]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        product_revision="003", include_investigations=True,
    )
    vs = [v for v in
          out["guided_investigations"]["official_cross_check"][
              "attribute_verifications"]
          if v["attribute"] == "revision"]
    assert vs[0]["state"] == "NOT_COMPARABLE"
    assert vs[0]["expected_value"] == "003"
    assert vs[0]["observed_value"] == "02"


def test_m4_multiplicity_ambiguity_versioned_divergence():
    out = _build(rows=[_row(0, "10020033")])
    divs = out["guided_investigations"]["official_cross_check"][
        "candidate_divergences"]
    assert len(divs) == 1
    d = divs[0]
    assert d["divergence_type"] == "MULTIPLICITY_AMBIGUITY"
    assert d["state"] == "UNKNOWN"
    assert d["official_value"] == ["O0002", "O0003"]
    assert d["observed_value"] == ["urow:0"]
    assert d["document_sha"] == _SHA


def test_m4_absent_observation_never_conflict():
    """Componente não lido → UNKNOWN, nunca CONFLICT."""
    out = _build()  # sem linhas
    vs = [v for v in
          out["guided_investigations"]["official_cross_check"][
              "attribute_verifications"]
          if v["attribute"] == "component_code"]
    assert all(v["state"] == "UNKNOWN" for v in vs)
    assert all(v["state"] != "CONFLICT" for v in
               out["guided_investigations"]["official_cross_check"][
                   "attribute_verifications"])


def test_m4_cross_check_present_even_fail_closed():
    out = build_object_profiles(
        bom_occurrences=[], visual_observations=[],
        understanding=_u(rows=[_row(0, "99999999")]),
        document_sha=_SHA, official_source_ref=_SRC,
        official_source_state="NOT_PROVIDED",
        include_investigations=True,
    )
    occ = out["guided_investigations"]["official_cross_check"]
    assert occ["multiplicity_analysis"] == {}
    assert occ["attribute_verifications"]


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
