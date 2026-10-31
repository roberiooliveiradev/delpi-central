"""Drawing analysis orchestration (E2–E3) — Documento 69.

Official-facts pipeline: product detail + structure (BOM) + drawing
metadata + drawing PDF (all via the delegated auxiliary gateway with
the caller's identity) → neutral text-layer extraction → evidence →
comparisons → structured DRAFT/CANDIDATE report. No LLM invocation —
no prompt-injection surface; extracted text is data, never instruction.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from engineering_app.application.drawing.description_rules import (
    validate_mp_description,
    validate_pi_description,
)
from engineering_app.application.drawing.drawing_comparator import (
    compare_observation_to_official,
    compare_observation_to_text,
    evaluate_source_match,
)
from engineering_app.application.drawing.drawing_evidence_extractor import (
    extract_evidence,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    PdfExtractionError,
    extract_pdf_text,
)
from engineering_app.domain.drawing import (
    DrawingAnalysisReport,
    DrawingEvidence,
    EvidenceClass,
    Finding,
    Verification,
    VerificationStatus,
)
from engineering_app.domain.drawing.source_identity import SourceMatch
from engineering_app.domain.drawing.visual_observation import (
    DrawingVisualObservation,
)

_MAX_BOM_ITEMS = 300


class DrawingAnalysisError(RuntimeError):
    """Analysis could not proceed; carries a stable error code."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _flatten_bom(node: Any, out: list[dict[str, Any]]) -> None:
    if not isinstance(node, dict):
        return
    for item in node.get("items") or []:
        if len(out) < _MAX_BOM_ITEMS:
            out.append(item)
        _flatten_bom(item, out)
    _flatten_bom(node.get("root"), out)


def _first_code_value(codes: list[str], official: str) -> bool:
    return official in set(codes)


async def analyze_product_drawing(
    *,
    code: str,
    source,
    ctx,
    visual_observations: list[DrawingVisualObservation] | None = None,
    scope: list[str] | None = None,
) -> dict[str, Any]:
    """Run the full drawing×product×BOM analysis for `code`."""
    # --- official facts (delegated identity) -------------------------------
    detail = await source.fetch_product_detail(ctx, code=code,
                                               view="engineering")
    if not detail or detail.get("status") == "not_found":
        raise DrawingAnalysisError(
            "product_not_found", f"Produto {code} não encontrado.", 404
        )
    drawing_meta = await source.fetch_product_drawing(ctx, code=code)
    found = bool(
        drawing_meta
        and drawing_meta.get("found")
        and drawing_meta.get("filename")
    )
    if not found:
        raise DrawingAnalysisError(
            "drawing_not_found",
            f"Produto {code} não possui desenho PDF oficial no acervo.",
            404,
        )
    pdf_result = await source.fetch_product_drawing_pdf(ctx, code=code)
    content = (pdf_result or {}).get("content") or b""
    if not content:
        raise DrawingAnalysisError(
            "drawing_pdf_unavailable",
            "Metadados do desenho existem mas o PDF não foi entregue.",
            502,
        )
    structure = await source.fetch_product_structure(
        ctx, code=code, max_depth=6, page_size=200
    )

    # --- extraction ---------------------------------------------------------
    try:
        extraction = extract_pdf_text(content)
    except PdfExtractionError as exc:
        raise DrawingAnalysisError(
            "pdf_extraction_failed", str(exc), 422
        ) from exc
    filename = str(drawing_meta.get("filename") or code)
    revision_meta = drawing_meta.get("revision")
    evidence = extract_evidence(
        extraction,
        document_ref=filename,
        source_revision=str(revision_meta) if revision_meta else None,
    )

    findings: list[Finding] = []
    verifications: list[Verification] = []
    fid = 0

    def add_finding(**kw: Any) -> None:
        nonlocal fid
        fid += 1
        findings.append(Finding(id=f"DRW-{fid:03d}", **kw))

    product = detail.get("product") or detail
    official_code = str(product.get("code") or code)
    official_desc = str(product.get("description") or "")
    official_type = str(product.get("product_type") or "")
    official_rev = str(product.get("current_revision") or "")
    drawing_ref = str(
        product.get("drawing_code") or drawing_meta.get("filename") or ""
    )

    # V1 — identification & legibility ---------------------------------------
    codes_in_drawing = [
        e.observed_value
        for e in evidence
        if e.evidence_type == "product_code_candidate"
    ]
    v = Verification(
        key="legibility",
        label="Desenho e legibilidade",
        status=(
            VerificationStatus.PASS
            if not extraction.scanned_or_empty
            else VerificationStatus.INCONCLUSIVE
        ),
        summary=(
            f"Camada de texto extraída: {extraction.pages_processed}/"
            f"{extraction.page_count} páginas, {extraction.text_chars} "
            "caracteres."
            if not extraction.scanned_or_empty
            else "Sem camada de texto — provável PDF escaneado; análise "
            "visual/OCR fora do adapter atual."
        ),
        limitations=extraction.limitations,
    )
    verifications.append(v)

    ident_ok = _first_code_value(codes_in_drawing, official_code)
    ident_status = (
        VerificationStatus.PASS
        if ident_ok
        else VerificationStatus.INCONCLUSIVE
    )
    verifications.append(
        Verification(
            key="product_identification",
            label="Identificação do produto no desenho",
            status=ident_status,
            summary=(
                f"Código {official_code} localizado no documento."
                if ident_ok
                else f"Código {official_code} não localizado na camada de "
                "texto — pode constar apenas graficamente (tabela/ISO)."
            ),
        )
    )
    if not ident_ok and not extraction.scanned_or_empty:
        add_finding(
            category="identification",
            severity="warning",
            severity_reason="Código do produto não identificado no texto.",
            rule="product_code_presence",
            rule_source="doc69 §8/E2.1",
            observed_value=sorted(set(codes_in_drawing))[:10],
            official_value=official_code,
            divergence="product_code_not_located_in_text_layer",
            confidence="medium",
            recommended_correction=(
                "Conferir legenda do desenho; código pode existir apenas "
                "graficamente (região/tabela)."
            ),
        )

    # V2 — revision ------------------------------------------------------------
    rev_values = sorted(
        {
            e.observed_value
            for e in evidence
            if e.evidence_type == "revision"
        }
        - {None}
    )
    if rev_values and official_rev:
        mismatch = [r for r in rev_values if r != official_rev]
        status = (
            VerificationStatus.WARNING if mismatch
            else VerificationStatus.PASS
        )
        if mismatch:
            add_finding(
                category="revision",
                severity="warning",
                severity_reason="Revisão do desenho difere do cadastro.",
                rule="drawing_revision_vs_product_current_revision",
                rule_source="api-delpi drawing metadata + SB1 B1_REVATU",
                observed_value=sorted(set(mismatch)),
                official_value=official_rev,
                divergence="revision_mismatch",
                confidence="medium",
                recommended_correction=(
                    "Verificar se o PDF no acervo é a revisão vigente."
                ),
            )
        summary = (
            f"Revisões no desenho {sorted(set(rev_values))} × "
            f"cadastro '{official_rev}'."
        )
    elif rev_values:
        status, summary = VerificationStatus.INCONCLUSIVE, (
            "Revisão no desenho encontrada mas produto não informa "
            "revisão vigente no contrato engineering."
        )
    else:
        status, summary = VerificationStatus.INCONCLUSIVE, (
            "Nenhuma revisão explícita identificada na camada de texto."
        )
    verifications.append(
        Verification(
            key="revision", label="Revisão", status=status, summary=summary
        )
    )

    # V3 — drawing × BOM --------------------------------------------------------
    bom_items: list[dict[str, Any]] = []
    if isinstance(structure, dict):
        _flatten_bom(structure, bom_items)

    text_blob = " ".join(p.text for p in extraction.pages).upper()
    matched, absent_in_text, uncertain = [], [], []
    for item in bom_items:
        icode = str(item.get("code") or "")
        if not icode:
            continue
        if icode in text_blob:
            matched.append(icode)
        elif extraction.scanned_or_empty:
            uncertain.append(icode)
        else:
            absent_in_text.append(icode)
    if extraction.scanned_or_empty:
        bom_status = VerificationStatus.INCONCLUSIVE
        bom_summary = "Sem texto — comparação visual não executada."
    else:
        missing_ratio = (
            len(absent_in_text) / len(bom_items) if bom_items else 0
        )
        bom_status = (
            VerificationStatus.WARNING if absent_in_text and missing_ratio <= 0.5
            else (
                VerificationStatus.PASS
                if bom_items
                else VerificationStatus.NOT_APPLICABLE
            )
        )
        bom_summary = (
            f"BOM oficial: {len(bom_items)} itens; "
            f"{len(matched)} códigos localizados no desenho; "
            f"{len(absent_in_text)} sem presença textual (podem constar "
            "somente graficamente — indício, não divergência comprovada)."
        )
    if absent_in_text and bom_items:
        add_finding(
            category="bom",
            severity="info",
            severity_reason=(
                "Ausência textual é indício — regra proíbe inferir "
                "exclusão da BOM por não-reconhecimento visual."
            ),
            rule="bom_code_presence_in_drawing",
            rule_source="doc69 §9 E3 — DRAWING_EVIDENCE ≠ OFFICIAL_BOM_FACT",
            observed_value=sorted(absent_in_text)[:15],
            official_value=f"{len(bom_items)} itens da estrutura",
            divergence="codes_without_text_presence",
            confidence="low",
            recommended_correction=(
                "Validação humana na tabela de itens do desenho."
            ),
        )
    verifications.append(
        Verification(
            key="bom_comparison",
            label="Desenho × estrutura (BOM)",
            status=bom_status,
            summary=bom_summary,
            evidence_class=EvidenceClass.CALCULATED,
        )
    )

    # V4 — MP / PI description rules -------------------------------------------
    mp = validate_mp_description(official_code, official_desc)
    pi = validate_pi_description(official_code, official_desc)
    root_status = {
        "PASS": VerificationStatus.PASS,
        "WARNING": VerificationStatus.WARNING,
        "INCONCLUSIVE": VerificationStatus.INCONCLUSIVE,
        "NOT_APPLICABLE": VerificationStatus.NOT_APPLICABLE,
    }
    verifications.append(
        Verification(
            key="mp_description",
            label="Descrição MP (produto raiz)",
            status=root_status[mp.status],
            summary=mp.summary,
        )
    )
    verifications.append(
        Verification(
            key="pi_description",
            label="Descrição PI 50xx (produto raiz)",
            status=root_status[pi.status],
            summary=pi.summary,
        )
    )
    mp_items_checked = 0
    mp_items_warned = 0
    pi_items_checked = 0
    pi_items_warned = 0
    for item in bom_items:
        icode = str(item.get("code") or "")
        idesc = str(item.get("description") or "")
        if re.match(r"^10\d{2}", icode):
            mp_items_checked += 1
            chk = validate_mp_description(icode, idesc)
            if chk.status == "WARNING":
                mp_items_warned += 1
                add_finding(
                    category="mp_description",
                    severity="warning",
                    severity_reason=chk.summary,
                    rule="mp_group_description_structure",
                    rule_source="Normas_Tecnicas_DELPI.md (grupos 1001-1025)",
                    observed_value=idesc,
                    official_value=icode,
                    divergence="mp_description_structure_deviation",
                    confidence="medium",
                    recommended_correction=(
                        "Conferir descrição cadastral contra a estrutura "
                        "canônica do grupo."
                    ),
                )
        elif re.match(r"^50\d{2}", icode):
            pi_items_checked += 1
            chk = validate_pi_description(icode, idesc)
            if chk.status == "WARNING":
                pi_items_warned += 1
                add_finding(
                    category="pi_description",
                    severity="warning",
                    severity_reason=chk.summary,
                    rule="pi_50xx_segment_structure",
                    rule_source="Understanding DELPI Intermediate Product Codes",
                    observed_value=idesc,
                    official_value=icode,
                    divergence="pi_segment_structure_deviation",
                    confidence="medium",
                    recommended_correction=(
                        "Conferir segmentos canônicos (isolação, cor 4L, "
                        "comprimento, decape, terminais)."
                    ),
                )
    verifications.append(
        Verification(
            key="mp_items_descriptions",
            label="Descrições MP da estrutura",
            status=(
                VerificationStatus.WARNING if mp_items_warned
                else (
                    VerificationStatus.PASS if mp_items_checked
                    else VerificationStatus.NOT_APPLICABLE
                )
            ),
            summary=(
                f"{mp_items_checked} itens MP verificados, "
                f"{mp_items_warned} com desvio estrutural."
            ),
            evidence_class=EvidenceClass.CALCULATED,
        )
    )
    verifications.append(
        Verification(
            key="pi_items_descriptions",
            label="Descrições PI 50xx da estrutura",
            status=(
                VerificationStatus.WARNING if pi_items_warned
                else (
                    VerificationStatus.PASS if pi_items_checked
                    else VerificationStatus.NOT_APPLICABLE
                )
            ),
            summary=(
                f"{pi_items_checked} itens 50xx verificados, "
                f"{pi_items_warned} com desvio de segmentos."
            ),
            evidence_class=EvidenceClass.CALCULATED,
        )
    )

    # V5 — notes / units / material hints ---------------------------------------
    notes = any(e.evidence_type == "technical_notes_present" for e in evidence)
    units = sorted(
        {e.observed_value for e in evidence if e.evidence_type == "unit"}
        - {None}
    )
    materials = [
        e for e in evidence if e.evidence_type == "material_hints"
    ]
    verifications.append(
        Verification(
            key="technical_notes",
            label="Notas técnicas",
            status=(
                VerificationStatus.PASS if notes
                else VerificationStatus.INCONCLUSIVE
            ),
            summary=(
                "Seção de notas identificada."
                if notes
                else "Nenhuma seção de notas identificada na camada de texto."
            ),
        )
    )
    verifications.append(
        Verification(
            key="units_dimensions",
            label="Unidades e indicações dimensionais",
            status=(
                VerificationStatus.PASS if units
                else VerificationStatus.INCONCLUSIVE
            ),
            summary=(
                f"Unidades identificadas: {', '.join(units[:8]) or '—'}."
                if units
                else "Nenhuma unidade explícita identificada."
            ),
        )
    )
    verifications.append(
        Verification(
            key="material_hints",
            label="Indicações de material/acabamento",
            status=(
                VerificationStatus.PASS if materials
                else VerificationStatus.INCONCLUSIVE
            ),
            summary=(
                f"Indicações: {materials[0].observed_value}."
                if materials
                else "Nenhuma indicação de material identificada."
            ),
        )
    )

    # V6 — pending contracts (honest) -------------------------------------------
    verifications.extend(
        [
            Verification(
                key="routing",
                label="Roteiro de fabricação",
                status=VerificationStatus.NOT_CHECKED,
                summary="Contrato de roteiro SG2 inexistente — "
                "OWNER_BLOCKED (doc69 §10/§17).",
            ),
            Verification(
                key="inspection",
                label="Inspeções vinculadas",
                status=VerificationStatus.NOT_CHECKED,
                summary="Contrato de inspeção por desenho não inventariado "
                "— TO_INVENTORY (doc69 §17).",
            ),
            Verification(
                key="pa_description",
                label="Descrição PA",
                status=VerificationStatus.NOT_CHECKED,
                summary="Sem norma de descrição PA na base autorizada — "
                "OWNER_BLOCKED (doc69 §9).",
            ),
        ]
    )

    # V7 — visual observations (untrusted consumer input) ----------------------
    visual_observations = visual_observations or []
    source_match = SourceMatch.UNKNOWN
    visual_results: list[dict[str, Any]] = []
    if visual_observations:
        source_match = evaluate_source_match(
            visual_observations,
            official_hash=extraction.document_hash,
            official_revision=(
                str(revision_meta) if revision_meta else official_rev or None
            ),
            official_document_ref=filename,
            official_product_code=official_code,
        )
        bom_code_set = {str(i.get("code") or "") for i in bom_items}
        text_conflicts = 0
        text_agreements = 0
        for obs in visual_observations:
            vs_text = (
                compare_observation_to_text(obs, text_blob)
                if source_match == SourceMatch.SAME_DOCUMENT_VERIFIED
                else {
                    "observation_id": obs.observation_id,
                    "status": "not_applicable",
                    "detail": (
                        f"identidade de fonte: {source_match.value} — "
                        "comparação visual×textual só é válida para o "
                        "mesmo documento verificado"
                    ),
                }
            )
            vs_official = compare_observation_to_official(
                obs,
                official_code=official_code,
                official_revision=official_rev or None,
                official_description=official_desc,
                bom_codes=bom_code_set,
            )
            if vs_text.get("status") == "conflict":
                text_conflicts += 1
            if vs_text.get("status") == "agreement":
                text_agreements += 1
            if vs_official.get("status") in {"conflict", "possible_divergence"}:
                add_finding(
                    category="visual_vs_official",
                    severity="warning",
                    severity_reason=(
                        f"Observação visual ({obs.kind}) diverge do fato "
                        "oficial — tratada como hipótese até revisão."
                    ),
                    rule="visual_observation_vs_official_fact",
                    rule_source="doc71 G3 §6.2-6.3 — input não confiável",
                    evidence_page=obs.page,
                    evidence_region=obs.view_or_region,
                    observed_value=obs.raw_observation,
                    official_value={
                        "code": official_code,
                        "revision": official_rev or None,
                    },
                    divergence=str(vs_official.get("detail") or ""),
                    confidence=obs.confidence,
                    recommended_correction=(
                        "Revisão humana do desenho × cadastro antes de "
                        "qualquer correção no TOTVS."
                    ),
                )
            visual_results.append(
                {
                    "observation": obs.to_dict(),
                    "vs_text_layer": vs_text,
                    "vs_official": vs_official,
                }
            )
        verifications.append(
            Verification(
                key="visual_observations",
                label="Observações visuais do consumidor",
                status=(
                    VerificationStatus.WARNING
                    if text_conflicts
                    else VerificationStatus.PASS
                ),
                summary=(
                    f"{len(visual_observations)} observações recebidas — "
                    f"identidade de fonte: {source_match.value}; "
                    f"{text_agreements} concordam com a camada de texto, "
                    f"{text_conflicts} em conflito de percepção."
                ),
                evidence_class=EvidenceClass.INFERRED,
                limitations=[
                    "observações visuais são entrada não confiável do "
                    "consumidor — jamais promovidas a fato oficial",
                    "comparação visual×textual só aplicada em "
                    "same_document_verified",
                ],
            )
        )
        if source_match != SourceMatch.SAME_DOCUMENT_VERIFIED:
            verifications.append(
                Verification(
                    key="visual_vs_textual",
                    label="Visual × extração textual",
                    status=VerificationStatus.NOT_CHECKED,
                    summary=(
                        f"Identidade de fonte '{source_match.value}' — "
                        "sem mesmo documento verificado, comparação "
                        "visual×textual não sustenta concordância nem "
                        "divergência comprovada."
                    ),
                )
            )
    else:
        verifications.append(
            Verification(
                key="visual_observations",
                label="Observações visuais do consumidor",
                status=VerificationStatus.NOT_APPLICABLE,
                summary="Nenhuma observação visual fornecida — análise "
                "restrita à extração textual × dados oficiais.",
            )
        )

    # --- report ---------------------------------------------------------------
    counts: dict[str, int] = {}
    for v_ in verifications:
        counts[v_.status] = counts.get(v_.status, 0) + 1
    report = DrawingAnalysisReport(
        identification={
            "product_code": official_code,
            "description": official_desc,
            "product_type": official_type,
            "current_revision": official_rev or None,
            "drawing_reference": drawing_ref or None,
            "drawing_file": filename,
            "drawing_revision": revision_meta,
            "analysis_source": "engineering-api product.drawing_analysis",
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        },
        executive_summary={
            "scope": "desenho oficial × cadastro × estrutura × descrições MP/PI",
            "verifications_total": len(verifications),
            "verifications_by_status": counts,
            "findings_total": len(findings),
            "bom_items_compared": len(bom_items),
            "evidence_items": len(evidence),
            "extraction_method": "pdf_text_layer (determinístico) — "
            "OCR/VLM fora do adapter atual",
            "human_review_required": True,
            "key_limitations": extraction.limitations + [
                "evidencia localizada por página (sem região/coordenada)",
                "ausência de presença textual não é divergência comprovada",
            ],
        },
        verifications=verifications,
        findings=findings,
        limitations=extraction.limitations,
        audit={
            "document_hash_sha256": extraction.document_hash,
            "pages_processed": extraction.pages_processed,
            "page_count": extraction.page_count,
            "identity": "delegated_user",
            "sources": [
                "api-delpi /products/{code}",
                "api-delpi /products/{code}/structure",
                "api-delpi /products/{code}/drawing(+pdf)",
            ],
            "write_operations": 0,
            "report_status": "DRAFT — artefato candidato à revisão "
            "do owner Engenharia; a EVA não aprova.",
        },
    )
    payload = report.to_dict()
    payload["contract_version"] = "drawing_analysis.v2"
    payload["source_match"] = source_match.value
    payload["visual_observations"] = [
        o.to_dict() for o in visual_observations
    ]
    payload["comparison_results"] = visual_results
    payload["scope"] = scope or ["all"]
    if visual_observations:
        payload["executive_summary"]["visual_observations_total"] = len(
            visual_observations
        )
    return payload
