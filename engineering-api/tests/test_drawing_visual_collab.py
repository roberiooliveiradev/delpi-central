"""Tests for ChatGPT visual collaboration contracts (doc 71 G1–G4)."""

from __future__ import annotations

import io

import pytest

from engineering_app.application.drawing.drawing_analysis_service import (
    analyze_product_drawing,
)
from engineering_app.application.drawing.drawing_comparator import (
    compare_observation_to_official,
    compare_observation_to_text,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    extract_pdf_text,
)
from engineering_app.domain.drawing.source_identity import (
    SourceMatch,
    classify_source_match,
)
from engineering_app.domain.drawing.visual_observation import (
    VisualObservationError,
    parse_visual_observations,
)
from tests.test_drawing_analysis import _minimal_pdf


def _obs(**kw):
    base = {
        "kind": "revision",
        "raw_observation": "REV 01",
        "document_identity": {"revision": "01", "product_code": "90264258"},
    }
    base.update(kw)
    return base


# --- observation schema ------------------------------------------------------


def test_parse_rejects_non_list():
    with pytest.raises(VisualObservationError):
        parse_visual_observations("x")


def test_parse_rejects_unknown_fields():
    with pytest.raises(VisualObservationError):
        parse_visual_observations([{"kind": "text", "raw_observation": "a",
                                    "evil_field": 1}])


def test_parse_rejects_bad_kind():
    with pytest.raises(VisualObservationError):
        parse_visual_observations([{"kind": "sql", "raw_observation": "a"}])


def test_parse_rejects_empty_text():
    with pytest.raises(VisualObservationError):
        parse_visual_observations([{"kind": "text"}])


def test_parse_accepts_and_normalizes():
    obs = parse_visual_observations([_obs()])
    assert len(obs) == 1
    assert obs[0].capture_method == "chatgpt_visual"
    assert obs[0].document_identity.revision == "01"


def test_parse_caps_count():
    payload = [_obs() for _ in range(60)]
    with pytest.raises(VisualObservationError):
        parse_visual_observations(payload)


# --- source identity ------------------------------------------------------------


def test_same_document_by_hash():
    m = classify_source_match(
        attachment_hash="abc", attachment_revision=None,
        attachment_document_ref=None, attachment_product_code=None,
        official_hash="abc", official_revision=None,
        official_document_ref=None, official_product_code=None,
    )
    assert m == SourceMatch.SAME_DOCUMENT_VERIFIED
    m2 = classify_source_match(
        attachment_hash="abc", attachment_revision=None,
        attachment_document_ref=None, attachment_product_code=None,
        official_hash="zzz", official_revision=None,
        official_document_ref=None, official_product_code=None,
    )
    assert m2 == SourceMatch.DIFFERENT_DOCUMENT


def test_revision_mismatch_is_different_document():
    m = classify_source_match(
        attachment_hash=None, attachment_revision="02",
        attachment_document_ref=None, attachment_product_code="90",
        official_hash=None, official_revision="01",
        official_document_ref=None, official_product_code="90",
    )
    assert m == SourceMatch.DIFFERENT_DOCUMENT


def test_lone_code_is_not_verified():
    m = classify_source_match(
        attachment_hash=None, attachment_revision=None,
        attachment_document_ref=None, attachment_product_code="90",
        official_hash=None, official_revision="01",
        official_document_ref="D.pdf", official_product_code="90",
    )
    assert m == SourceMatch.POSSIBLE_MATCH


# --- comparator ----------------------------------------------------------------


def test_revision_agreement_vs_text():
    obs = parse_visual_observations([_obs()])[0]
    r = compare_observation_to_text(obs, "PRODUTO 90264258 REV 01 UNIDADE PC")
    assert r["status"] == "agreement"


def test_revision_conflict_vs_text():
    obs = parse_visual_observations(
        [_obs(raw_observation="REV 09", normalized_value="09")]
    )[0]
    r = compare_observation_to_text(obs, "PRODUTO 90264258 REV 01 PC")
    assert r["status"] == "conflict"


def test_official_revision_conflict():
    obs = parse_visual_observations(
        [_obs(raw_observation="REV 02", normalized_value="02")]
    )[0]
    r = compare_observation_to_official(
        obs, official_code="90264258", official_revision="01",
        official_description="D", bom_codes=set(),
    )
    assert r["status"] == "conflict"


def test_bom_item_possible_divergence():
    obs = parse_visual_observations(
        [_obs(kind="bom_item", raw_observation="ITEM 99999999 FALSO")]
    )[0]
    r = compare_observation_to_official(
        obs, official_code="90264258", official_revision=None,
        official_description="D", bom_codes={"10011234"},
    )
    assert r["status"] == "possible_divergence"


# --- service with observations ------------------------------------------------


class _FakeSource:
    def __init__(self, pdf):
        self._pdf = pdf

    async def fetch_product_detail(self, ctx, *, code, view="engineering"):
        return {"product": {"code": code,
                            "description": "CONJUNTO TESTE",
                            "product_type": "PA",
                            "current_revision": "01"}}

    async def fetch_product_drawing(self, ctx, *, code):
        return {"found": True, "filename": "D.pdf", "revision": "01"}

    async def fetch_product_drawing_pdf(self, ctx, *, code):
        return {"status": "available", "content": self._pdf}

    async def fetch_product_structure(self, ctx, **kw):
        return {"root": {"items": [{"code": "10011234",
                                    "description": "CABO FLEX PT"}]}}


async def test_analysis_with_visual_observations():
    pdf = _minimal_pdf("PRODUTO 90264258 DESENHO REV 01 CABO FLEX PC UN")
    extraction = extract_pdf_text(pdf)
    import hashlib

    obs = parse_visual_observations([
        _obs(raw_observation="REV 01",
             document_identity={"revision": "01",
                                "product_code": "90264258",
                                "document_hash": extraction.document_hash,
                                "document_ref": "D.pdf"})
    ])
    report = await analyze_product_drawing(
        code="90264258", source=_FakeSource(pdf), ctx=None,
        visual_observations=obs,
    )
    assert report["source_match"] == "same_document_verified"
    assert report["visual_observations"]
    assert report["contract_version"] == "drawing_analysis.v2"
    assert report["comparison_results"][0]["vs_text_layer"]["status"] == (
        "agreement"
    )


async def test_analysis_unknown_source_marks_not_checked():
    pdf = _minimal_pdf("PRODUTO 90264258 DESENHO REV 01 CABO FLEX PC UN")
    obs = parse_visual_observations([
        _obs(raw_observation="REV 01",
             document_identity={"source": "user_attachment"})
    ])
    report = await analyze_product_drawing(
        code="90264258", source=_FakeSource(pdf), ctx=None,
        visual_observations=obs,
    )
    keys = {v["key"]: v["status"] for v in report["verifications"]}
    assert keys["visual_vs_textual"] == "NOT_CHECKED"
    assert report["source_match"] in {"unknown", "possible_match"}


async def test_backward_compatible_without_observations():
    pdf = _minimal_pdf("PRODUTO 90264258 DESENHO REV 01 CABO FLEX PC UN")
    report = await analyze_product_drawing(
        code="90264258", source=_FakeSource(pdf), ctx=None
    )
    keys = {v["key"]: v["status"] for v in report["verifications"]}
    assert keys["visual_observations"] == "NOT_APPLICABLE"
    assert report["visual_observations"] == []
