"""R4 regression — typed identifiers, visual revision provenance, BOM stats."""

from __future__ import annotations

from engineering_app.application.drawing.drawing_analysis_service import (
    analyze_product_drawing,
)
from engineering_app.application.drawing.drawing_comparator import (
    _label_classified_identifiers,
    compare_observation_to_official,
)
from engineering_app.domain.drawing.visual_observation import (
    parse_visual_observations,
)
from tests.test_drawing_analysis_r2 import PDF_90264302, _EnvelopeSource


def test_label_classification_no_false_product_conflict():
    """COD/DES labels classify identifiers by role — only PRODUTO-label
    compares against official product_code."""
    ids = _label_classified_identifiers(
        "Produto 90264302, COD cliente 18702881, DES desenho 10013396831."
    )
    roles = {i["role"]: i["value"] for i in ids}
    assert roles.get("customer_reference") == "18702881"
    assert roles.get("drawing_code") == "10013396831"
    assert roles.get("product_code") == "90264302"


def test_official_comparison_three_identifiers_no_conflict():
    obs = parse_visual_observations([{
        "kind": "identification",
        "raw_observation": "Produto 90264302, COD 18702881, DES 10013396831",
    }])[0]
    r = compare_observation_to_official(
        obs, official_code="90264302", official_revision=None,
        official_description="D", bom_codes=set(),
    )
    assert r["status"] == "agreement"


def test_official_comparison_wrong_product_code_conflicts():
    obs = parse_visual_observations([{
        "kind": "identification",
        "raw_observation": "Produto 90264399",
    }])[0]
    r = compare_observation_to_official(
        obs, official_code="90264302", official_revision=None,
        official_description="D", bom_codes=set(),
    )
    # unlabeled 90264399 is unknown_identifier → not compared → no_evidence
    assert r["status"] in {"no_evidence", "conflict"}


async def test_typed_identifiers_in_payload():
    obs = parse_visual_observations([{
        "kind": "identification",
        "raw_observation": "title block",
        "identifiers": [
            {"role": "product_code", "value": "90264302"},
            {"role": "customer_reference", "value": "18702881"},
            {"role": "drawing_code", "value": "10013396831"},
        ],
    }])
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None,
        visual_observations=obs,
    )
    cr = report["comparison_results"][0]
    assert cr["vs_official"]["status"] == "agreement"
    assert report["visual_observations"][0]["identifiers"][1]["role"] == (
        "customer_reference"
    )


async def test_visual_revision_presented_not_promoted():
    obs = parse_visual_observations([{
        "kind": "revision", "raw_observation": "REV 00",
        "normalized_value": "00", "page": 1,
        "document_identity": {"product_code": "90264302"},
    }])
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None,
        visual_observations=obs,
    )
    domains = report["identification"]["revision_domains"]
    assert domains["customer_totvs_revision"] == "001"
    assert domains["engineering_drawing_revision_visual"]["values"] == ["00"]
    assert domains["engineering_drawing_revision_visual"][
        "promoted_to_official"] is False
    assert domains["totvs_vs_drawing_comparable"] is False
    assert domains["rule"] == "ENG-REV-001"
    assert not any(
        f["category"] == "revision" for f in report["findings"]
    )


async def test_bom_stats_occurrences_vs_unique():
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None
    )
    stats = report["executive_summary"]["bom_stats"]
    assert stats["total_occurrences"] == 4
    assert stats["unique_codes"] == 4
    assert stats["by_type"].get("PI") == 2
    assert stats["by_type"].get("MP") == 2
