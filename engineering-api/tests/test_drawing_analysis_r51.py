"""R5.1 stabilization — reconciliation/findings consistency regression.

Reproduces the real defect: reconciliation_status=visual_and_official_only
coexisting with an identification WARNING caused solely by text-layer
absence. Root cause: reclassification filter matched nonexistent
category names.
"""

from __future__ import annotations

from engineering_app.application.drawing.drawing_analysis_service import (
    analyze_product_drawing,
)
from engineering_app.domain.drawing.visual_observation import (
    parse_visual_observations,
)
from tests.test_drawing_analysis import _minimal_pdf
from tests.test_drawing_analysis_r2 import _EnvelopeSource

# PDF sem o código do produto na camada textual — força a ausência que
# produzia o falso WARNING na R5.
PDF_NO_CODE = _minimal_pdf(
    "CHICOTE DE LIGACAO REV 00 CABO 643MM 663MM TERM PINO PC UN"
)

OBS_IDENT = {
    "kind": "identification",
    "raw_observation":
        "Produto 90264302, COD 18702881, DES 10013396831",
    "page": 1,
    "view_or_region": "quadro superior direito",
    "confidence": "high",
    "identifiers": [
        {"role": "product_code", "value": "90264302"},
        {"role": "customer_reference", "value": "18702881"},
        {"role": "drawing_code", "value": "10013396831"},
    ],
    "document_identity": {"product_code": "90264302"},
}


async def test_s1_visual_agreement_no_identification_warning():
    """S1/S8: reconciliado visual×oficial — ausência textual vira info."""
    obs = parse_visual_observations([OBS_IDENT])
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_NO_CODE), ctx=None,
        visual_observations=obs,
    )
    recon = [
        r for r in report["reconciliations"]
        if r["subject"] == "product_code"
    ][0]
    assert recon["reconciliation_status"] == "visual_and_official_only"
    assert recon["visual_evidence"] is True
    assert recon["official_evidence"] is True
    assert recon["textual_evidence"] is False

    # INV-02: nenhum WARNING de identificação por ausência textual.
    ident_warnings = [
        f for f in report["findings"]
        if f["category"] == "identification" and f["severity"] == "warning"
    ]
    assert ident_warnings == []
    recon_findings = [
        f for f in report["findings"]
        if f["divergence"] == "text_coverage_limitation"
    ]
    assert recon_findings and all(
        f["severity"] == "info" for f in recon_findings
    )


async def test_s8_real_divergence_still_detected():
    """INV-03: product_code visual divergente continua divergência."""
    obs = parse_visual_observations([{
        "kind": "identification",
        "raw_observation": "Produto 90264399 observado",
        "identifiers": [{"role": "product_code", "value": "90264399"}],
    }])
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_NO_CODE), ctx=None,
        visual_observations=obs,
    )
    vs = report["comparison_results"][0]["vs_official"]
    assert vs["status"] == "conflict"


async def test_s6_bom_relationship_semantics():
    """S6: vínculos raiz→diretos e aninhados separados e explícitos."""
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_NO_CODE), ctx=None
    )
    stats = report["executive_summary"]["bom_stats"]
    assert stats["root_child_links"] == 2          # PA→PI 50226113/114
    assert stats["nested_parent_links"] == 4       # PI→MP ×4
    assert stats["total_relationships"] == 6
    assert stats["direct_children"] == 2
    ocurrences = report["bom_occurrences"]
    pis = [o for o in ocurrences if o["component_code"].startswith("5022")]
    mps = [o for o in ocurrences if o["component_code"].startswith("100")]
    assert all(o["parent_code"] == "90264302" for o in pis)
    assert {o["parent_code"] for o in mps} == {"50226113", "50226114"}
    assert {o["depth"] for o in pis} == {1}
    assert {o["depth"] for o in mps} == {2}
