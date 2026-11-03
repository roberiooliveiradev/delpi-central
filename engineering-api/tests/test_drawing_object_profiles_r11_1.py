"""R11.1 — integração dos perfis de desenho à evidência visual real.

Cobre: identidade de documento, separação proveniência oficial×visual,
mapper understanding→DrawingObjectSet (válidos, ambíguos, rejeitados),
relações com evidência, semântica de quantidades, casos negativos e
ausência de dependências externas no domínio.
"""

from __future__ import annotations

import hashlib
import inspect

import pytest

from engineering_app.application.drawing.drawing_analysis_service import (
    analyze_product_drawing,
)
from engineering_app.application.drawing.object_profiles_builder import (
    build_object_profiles,
)
from engineering_app.application.drawing.understanding import (
    build_understanding,
)
from tests.test_drawing_analysis_r2 import _EnvelopeSource, PDF_90264302

_PDF_SHA = hashlib.sha256(PDF_90264302).hexdigest()
_SRC_REF = "api-delpi:/products/90264302/structure"

_BOM = [
    {"occurrence_id": "O0001", "component_code": "50226113",
     "component_type": "PI", "parent_code": "90264302", "depth": 1,
     "path": "50226113", "quantity_raw": "1", "unit_raw": "PC"},
    {"occurrence_id": "O0002", "component_code": "10020033",
     "component_type": "MP", "parent_code": "50226113", "depth": 2,
     "path": "50226113/10020033", "quantity_raw": "643",
     "unit_raw": "MT"},
    {"occurrence_id": "O0003", "component_code": "10020033",
     "component_type": "MP", "parent_code": "50226114", "depth": 2,
     "path": "50226114/10020033", "quantity_raw": "643",
     "unit_raw": "MT"},
    {"occurrence_id": "O0004", "component_code": "10080106",
     "component_type": "MP", "parent_code": "50226113", "depth": 2,
     "path": "50226113/10080106", "quantity_raw": "1000",
     "unit_raw": "PC"},
]


def _cell(text, col, col_type=None, box=None, ambiguous=False):
    c = {
        "text": text, "col": col, "row": 0,
        "bounding_box_px": box or [10, 10, 30, 10, 30, 20, 10, 20],
    }
    if col_type:
        c["col_type"] = col_type
    if ambiguous:
        c["ambiguous"] = True
        c["alternatives"] = [col, col + 1]
    return c


def _field(text, col, box=None):
    return {
        "raw_text": text, "normalized_value": text,
        "bounding_box_px": box or [10, 10, 30, 10, 30, 20, 10, 20],
        "col": col,
        "association_method": "col_type_header_or_content",
        "association_state": "FIELD_IDENTIFIED",
    }


def _row(i, *, item=None, qty=None, code=None, desc=None,
         fields=None, assoc="FIELD_IDENTIFIED", cells=None):
    f = dict(fields) if fields is not None else {}
    if item is not None:
        f.setdefault("item", _field(item, 0))
    if qty is not None:
        f.setdefault("quantity", _field(qty, 1))
    if code is not None:
        f.setdefault("component_code", _field(code, 2, box=[
            600, 400 + i * 20, 660, 400 + i * 20,
            660, 410 + i * 20, 600, 410 + i * 20]))
    if desc is not None:
        f.setdefault("description", _field(desc, 3))
    return {
        "row": i, "y_px": 400 + i * 20,
        "cells": cells if cells is not None else [
            _cell(v, k, k) for k, v in {
                "item": item, "quantity": qty,
                "component_code": code, "description": desc,
            }.items() if v is not None
            for k in [0]  # col index simplified
        ],
        "col_count": 4,
        "fields": f,
        "item": item, "quantity": qty,
        "component_code": code, "description": desc,
        "association_status": assoc,
    }


def _u(rows=None, dims=None, regions=None, balloons=None, sha=_PDF_SHA,
       bom_comparison=None, conflicts=None, geo_regions=None):
    return {
        "schema_version": "drawing_understanding.v1",
        "document_hash_sha256": sha,
        "page": 1,
        "regions": regions or [],
        "component_table": {
            "candidate": bool(rows),
            "rows": rows or [],
            "row_count": len(rows or []),
            "unreliable_boundary": False,
        },
        "dimension_candidates": dims or [],
        "geometry_regions": geo_regions or [],
        "balloons": balloons or [],
        "ownership_conflicts": conflicts or [],
        "bom_comparison": bom_comparison,
        "limitations": [],
    }


def _dim(text, box, region="drawing_area", state="DIMENSION_TEXT_FOUND"):
    return {
        "text": text, "region": region, "page": 1,
        "bounding_box_px": box, "state": state,
        "association": None, "rule": "explicit_tolerance_or_unit",
        "limitations": [],
    }


def _objects(out):
    return {o["object_id"]: o for o in out["objects"]}


# 1/2 — identidade do documento e separação de proveniência -------------


async def test_document_identity_propagated_from_audit_hash():
    """object_profiles.document_sha = audit.document_hash_sha256 real."""
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None
    )
    op = report["object_profiles"]
    assert op["document_sha"] == _PDF_SHA
    assert op["document_sha"] == report["audit"]["document_hash_sha256"]
    assert op["document_identity"]["set_document_sha"] == _PDF_SHA


def test_official_vs_visual_provenance_separated():
    """Ocorrência BOM ≠ evidência visual: identidade própria por fonte."""
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=_u(rows=[_row(0, item="1", qty="1",
                                    code="10020033", desc="CABO")]),
        document_sha=_PDF_SHA, official_source_ref=_SRC_REF,
    )
    objs = _objects(out)
    occ = objs["O0001"]
    assert occ["official"] is True
    assert occ["document_identity"] == _SRC_REF
    assert occ["document_identity"] != _PDF_SHA
    item = objs["urow:0"]
    assert item["official"] is False
    assert item["document_identity"] == _PDF_SHA
    # evidências visuais referenciam o PDF; oficiais não
    assert all(
        r["document_sha"] == _PDF_SHA for r in item["evidence_refs"]
    )


# 3 — conversão de observações válidas ----------------------------------


def test_valid_observations_become_objects():
    u = _u(
        rows=[_row(0, item="1", qty="2", code="10020033",
                   desc="CABO FLEX")],
        dims=[_dim("643±2", [200, 300, 240, 300, 240, 310, 200, 310])],
    )
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    objs = _objects(out)
    it = objs["urow:0"]
    assert it["object_type"] == "drawing_table_item"
    assert it["attributes"]["item_label"] == "1"
    assert it["attributes"]["assembly_quantity"] == "2"
    assert it["attributes"]["component_code_candidate"] == "10020033"
    assert "ambiguities" not in it["attributes"]
    assert it["evidence_refs"]
    ref = it["evidence_refs"][0]
    assert ref["page"] == 1
    assert ref["bounding_box"]
    assert ref["coordinate_system"] == "pixels_pdfium_top_left"
    d = objs["udim:0"]
    assert d["object_type"] == "dimension"
    assert d["observation_state"] == "OBSERVED"


# 4 — ambiguidade preservada, nunca promovida ----------------------------


def test_ambiguous_observations_marked_not_promoted():
    u = _u(rows=[
        _row(0, item="1", qty="1/2", code="10020033",
             desc="QTD FRACIONADA"),                      # qty não numérica
        _row(1, item="2", qty="1", code="1008-CABO-FLEX",
             desc="CODIGO MISTO"),                        # código inválido
        _row(2, assoc="UNRESOLVED", fields={}),           # não resolvida
    ])
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    objs = _objects(out)
    a = objs["urow:0"]["attributes"]
    assert "quantity_not_numeric" in a["ambiguities"]
    assert a["assembly_quantity"] is None
    assert a["assembly_quantity_raw"] == "1/2"   # evidência bruta preservada
    b = objs["urow:1"]["attributes"]
    assert "component_code_not_code_shaped" in b["ambiguities"]
    assert b["component_code_candidate"] is None
    assert b["component_code_candidate_raw"] == "1008-CABO-FLEX"
    c = objs["urow:2"]["attributes"]
    assert "association_unresolved" in c["ambiguities"]
    # nenhuma relação promovida a partir de evidência ambígua
    assert out["relations"] == []
    assert out["ambiguous_observations"] == 3


# 5/6 — relações com evidência e integridade referencial ----------------


def test_relations_composed_with_evidence_and_integrity():
    u = _u(rows=[_row(0, item="1", qty="1", code="10080106")])
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    rels = out["relations"]
    assert len(rels) == 1
    rel = rels[0]
    assert rel["relation_type"] == "REPRESENTED_BY"
    assert rel["source_object_id"] == "O0004"
    assert rel["target_object_id"] == "urow:0"
    assert rel["verification_state"] == "NOT_CHECKED"
    assert rel["uncertainty_reason"]
    assert rel["evidence_refs"]
    assert rel["evidence_refs"][0]["raw_value"] == "10080106"
    ids = set(_objects(out))
    for r in rels:
        assert r["source_object_id"] in ids
        assert r["target_object_id"] in ids


def test_full_chain_item_balloon_geometry_dimension():
    """item→balão→geometria e cota→geometria só com evidência real."""
    geo = [{"id": "g1", "type": "geometry",
            "box_px": [100, 200, 500, 400]}]
    u = _u(
        rows=[_row(0, item="7", qty="1", code="10020033")],
        geo_regions=geo,
        balloons=[{"item_label": "7", "points_to": "g1",
                   "bounding_box_px": [50, 60, 70, 60, 70, 80, 50, 80]}],
        dims=[_dim("643±2", [200, 300, 240, 300, 240, 310, 200, 310])],
    )
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    by_type = out["relations_by_type"]
    assert by_type.get("REFERENCED_BY") == 1   # item → balão
    assert by_type.get("POINTS_TO") == 1       # balão → geometria
    assert by_type.get("DIMENSIONS") == 1      # cota → geometria
    assert by_type.get("REPRESENTED_BY") == 2  # 2 ocorrências 10020033


# 7/8/9 — casos de correspondência ---------------------------------------


def test_known_component_without_observation():
    """Código da BOM sem linha na tabela: objeto existe, sem relação."""
    u = _u(rows=[_row(0, item="1", qty="1", code="10020033")])
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    objs = _objects(out)
    assert objs["O0004"]["attributes"]["component_code"] == "10080106"
    related = {r["source_object_id"] for r in out["relations"]}
    assert "O0004" not in related


def test_observation_without_bom_counterpart():
    """Código na tabela fora da BOM: objeto preservado, sem relação."""
    u = _u(rows=[_row(0, item="1", qty="1", code="99999999")])
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    objs = _objects(out)
    assert objs["urow:0"]["attributes"][
        "component_code_candidate"] == "99999999"
    assert out["relations"] == []


def test_two_bom_occurrences_same_code_both_related():
    """Duas ocorrências do mesmo código → uma relação por ocorrência."""
    u = _u(rows=[_row(0, item="1", qty="2", code="10020033")])
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    rels = out["relations"]
    assert len(rels) == 2
    assert {r["source_object_id"] for r in rels} == {"O0002", "O0003"}
    assert all(r["target_object_id"] == "urow:0" for r in rels)


# 10 — semântica de quantidades ------------------------------------------


def test_quantity_semantics_never_compared():
    """500mm de consumo ≠ 1 un de montagem ≠ cota — sem equivalência."""
    occ = [dict(_BOM[1])]
    occ[0]["quantity_raw"] = "500"
    occ[0]["unit_raw"] = "mm"
    u = _u(rows=[_row(0, item="1", qty="1", code="10020033")],
           dims=[_dim("500mm", [1, 1, 30, 1, 30, 10, 1, 10])])
    out = build_object_profiles(
        bom_occurrences=occ, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    objs = _objects(out)
    assert objs["O0002"]["attributes"]["consumption_quantity"] == "500"
    assert objs["O0002"]["attributes"]["consumption_unit"] == "mm"
    assert objs["urow:0"]["attributes"]["assembly_quantity"] == "1"
    assert objs["udim:0"]["attributes"]["unit"] == "mm"
    # nenhuma verificação afirma equivalência consumo×montagem×cota
    assert all(
        v == "NOT_CHECKED"
        for o in out["objects"]
        for v in [o["verification_state"]]
    )
    assert any(
        "consumo" in lim and "montagem" in lim
        for lim in out["limitations"]
    )


# 11 — identidade de documento incompatível ------------------------------


def test_incompatible_document_identity_flagged():
    """understanding de outro documento → conflito explícito, não merge."""
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=_u(rows=[_row(0, item="1", qty="1",
                                    code="10020033")], sha="sha-other"),
        document_sha=_PDF_SHA, official_source_ref=_SRC_REF,
    )
    ident = out["document_identity"]
    assert ident["set_document_sha"] == _PDF_SHA
    assert ident["understanding_document_sha"] == "sha-other"
    assert ident["match"] is False
    # objeto visual carrega a identidade do SEU documento — não a do set
    assert _objects(out)["urow:0"]["document_identity"] == "sha-other"


# 12 — ausência de geometria/balão honesta --------------------------------


def test_absent_geometry_and_balloon_zero_relations_with_limitations():
    u = _u(rows=[_row(0, item="1", qty="1", code="10020033")],
           dims=[_dim("643±2", [1, 1, 30, 1, 30, 10, 1, 10])])
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    assert "POINTS_TO" not in out["relations_by_type"]
    assert "DIMENSIONS" not in out["relations_by_type"]
    assert "REFERENCED_BY" not in out["relations_by_type"]
    assert any("balões" in lim for lim in out["limitations"])
    assert any("geometria" in lim for lim in out["limitations"])


# 13 — relatório existente preservado -------------------------------------


async def test_existing_report_preserved_without_understanding():
    """Sem understanding: contrato do relatório intacto, perfis BOM-only."""
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None
    )
    for key in (
        "identification", "executive_summary", "verifications",
        "findings", "audit", "sections", "bom_occurrences",
        "object_profiles", "contract_version",
    ):
        assert key in report
    op = report["object_profiles"]
    assert op["understanding_integrated"] is False
    assert op["objects_by_type"] == {"bom_occurrence": 6}
    assert op["relations"] == []


async def test_service_understanding_feeds_profiles():
    """analyze() com understanding → perfis visuais + mesma identidade."""
    u = _u(rows=[_row(0, item="1", qty="1", code="10020033")])
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None,
        understanding=u,
    )
    op = report["object_profiles"]
    assert op["understanding_integrated"] is True
    assert op["document_identity"]["match"] is True
    assert op["objects_by_type"]["drawing_table_item"] == 1
    assert op["relations_by_type"].get("REPRESENTED_BY") == 2


# 14 — domínio sem dependências externas -----------------------------------


def test_domain_no_external_dependencies():
    """domain/drawing permanece puro: sem OCR/HTTP/framework/DB."""
    import engineering_app.domain.drawing.object_profiles as m

    src = inspect.getsource(m)
    for bad in (
        "cv2", "paddle", "pypdfium2", "requests", "httpx",
        "sqlalchemy", "fastapi", "flask", "urllib",
    ):
        assert bad not in src


def test_mapper_uses_real_understanding_output():
    """Caso irmão: mapper sobre saída real de build_understanding."""
    toks = [
        {"text": "COMPONENTE", "bounding_box_px": [600, 380, 650, 380,
         650, 390, 600, 390], "confidence": 0.9},
        {"text": "QTD", "bounding_box_px": [700, 380, 730, 380,
         730, 390, 700, 390], "confidence": 0.9},
        {"text": "10020033", "bounding_box_px": [600, 400, 660, 400,
         660, 410, 600, 410], "confidence": 0.9},
        {"text": "1", "bounding_box_px": [700, 400, 710, 400,
         710, 410, 700, 410], "confidence": 0.9},
        {"text": "10080106", "bounding_box_px": [600, 420, 660, 420,
         660, 430, 600, 430], "confidence": 0.9},
        {"text": "2", "bounding_box_px": [700, 420, 710, 420,
         710, 430, 700, 430], "confidence": 0.9},
        {"text": "COD", "bounding_box_px": [620, 700, 650, 700,
         650, 710, 620, 710], "confidence": 0.9},
        {"text": "REV", "bounding_box_px": [620, 720, 650, 720,
         650, 730, 620, 730], "confidence": 0.9},
        {"text": "643±2", "bounding_box_px": [200, 300, 240, 300,
         240, 310, 200, 310], "confidence": 0.9},
    ]
    u = build_understanding(
        toks, document_hash=_PDF_SHA, bom_codes=["10020033", "10080106"],
        product_code="90264302", render_size_px=(840, 730),
    )
    out = build_object_profiles(
        bom_occurrences=_BOM, visual_observations=[],
        understanding=u, document_sha=_PDF_SHA,
        official_source_ref=_SRC_REF,
    )
    items = [
        o for o in out["objects"]
        if o["object_type"] == "drawing_table_item"
    ]
    assert len(items) == 2
    assert out["objects_by_type"].get("dimension") == 1
    assert out["relations_by_type"].get("REPRESENTED_BY") == 3
