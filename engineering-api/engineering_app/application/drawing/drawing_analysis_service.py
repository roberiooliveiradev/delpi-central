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
from engineering_app.application.drawing.drawing_contracts import (
    DrawingAnalysisError,
    unwrap_delegated,
)
from engineering_app.application.drawing.extraction_ports import (
    get_default_extractor,
)
from engineering_app.domain.drawing.source_identity import SourceMatch
from engineering_app.domain.drawing.visual_observation import (
    DrawingVisualObservation,
)

__all__ = ["DrawingAnalysisError", "analyze_product_drawing"]

_MAX_BOM_ITEMS = 300


def _flatten_bom(
    node: Any,
    out: list[dict[str, Any]],
    *,
    parent_code: str | None = None,
    depth: int = 0,
    path: str = "",
) -> None:
    """Multi-level traversal (R5-C): every occurrence gets deterministic
    parent_code/depth/path provenance — the same component code under
    different branches yields distinct occurrences."""
    if not isinstance(node, dict):
        return
    effective_parent = str(node.get("code") or "") or parent_code
    for key in ("items", "components", "children"):
        for item in node.get(key) or []:
            code = str(item.get("code") or "")
            occ_path = f"{path}/{code}" if path else code
            enriched = dict(item)
            enriched["_occurrence_id"] = f"O{len(out) + 1:04d}"
            enriched["_parent_code"] = effective_parent
            enriched["_depth"] = depth + 1
            enriched["_path"] = occ_path
            if len(out) < _MAX_BOM_ITEMS:
                out.append(enriched)
            _flatten_bom(
                item, out,
                parent_code=code or parent_code,
                depth=depth + 1,
                path=occ_path,
            )
    _flatten_bom(
        node.get("root"), out, parent_code=effective_parent,
        depth=depth, path=path,
    )


def _first_code_value(codes: list[str], official: str) -> bool:
    return official in set(codes)


def flatten_bom_occurrences(
    structure: Any, code: str
) -> list[dict[str, Any]]:
    """Ocorrências BOM achatadas com proveniência determinística —
    projeção canônica consumida pelo relatório e pelos perfis R11."""
    items: list[dict[str, Any]] = []
    if isinstance(structure, dict):
        _flatten_bom(structure, items, parent_code=code)
    return [
        {
            "occurrence_id": i.get("_occurrence_id"),
            "component_code": i.get("code"),
            "component_type": i.get("product_type") or i.get("type"),
            "parent_code": i.get("_parent_code"),
            "depth": i.get("_depth"),
            "path": i.get("_path"),
            "quantity_raw": i.get("quantity"),
            "unit_raw": i.get("unit"),
        }
        for i in items
    ]


async def analyze_product_drawing(
    *,
    code: str,
    source,
    ctx,
    visual_observations: list[DrawingVisualObservation] | None = None,
    scope: list[str] | None = None,
    extractor=None,
    understanding: dict[str, Any] | None = None,
    progressive: dict[str, Any] | None = None,
    drawing_tokens: list[dict[str, Any]] | None = None,
    prefetched: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the full drawing×product×BOM analysis for `code`."""
    # --- official facts (delegated identity) -------------------------------
    # DEC-VAL-032: `prefetched` permite que o chamador execute as
    # leituras delegadas enquanto a credencial do usuário está válida
    # (jobs prolongados — OCR posterior não exige autenticação).
    _pf = prefetched or {}
    detail_raw = _pf.get("detail_raw") or await source.fetch_product_detail(
        ctx, code=code, view="engineering"
    )
    detail = unwrap_delegated(
        detail_raw,
        what="product.detail",
        not_found_code="product_not_found",
        not_found_message=f"Produto {code} não encontrado.",
    )
    drawing_meta_raw = _pf.get(
        "drawing_meta_raw"
    ) or await source.fetch_product_drawing(ctx, code=code)
    drawing_meta = unwrap_delegated(
        drawing_meta_raw,
        what="product.drawing",
        not_found_code="drawing_not_found",
        not_found_message=(
            f"Produto {code} não possui desenho PDF oficial no acervo."
        ),
    )
    found = bool(
        drawing_meta.get("found") and drawing_meta.get("filename")
    )
    if not found:
        raise DrawingAnalysisError(
            "drawing_not_found",
            f"Produto {code} não possui desenho PDF oficial no acervo.",
            404,
        )
    pdf_result = _pf.get(
        "pdf_result"
    ) or await source.fetch_product_drawing_pdf(ctx, code=code)
    content = (pdf_result or {}).get("content") or b""
    if not content:
        raise DrawingAnalysisError(
            "drawing_pdf_unavailable",
            "Metadados do desenho existem mas o PDF não foi entregue.",
            502,
        )
    structure_raw = _pf.get(
        "structure_raw"
    ) or await source.fetch_product_structure(
        ctx, code=code, max_depth=6, page_size=200
    )
    try:
        structure = unwrap_delegated(
            structure_raw,
            what="product.structure",
            not_found_code="structure_not_found",
            not_found_message="",
        )
    except DrawingAnalysisError as exc:
        structure = {}
        structure_error = exc
    else:
        structure_error = None

    # --- extraction ---------------------------------------------------------
    try:
        # R6-B: extractor injetado ou default do composition root.
        if extractor is None:
            extractor = get_default_extractor()
        extraction = extractor.extract(content)
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

    # V2 — revision domains (ENG-REV-001: TOTVS/cliente ≠ desenho/engenharia)
    rev_values = sorted(
        {
            e.observed_value
            for e in evidence
            if e.evidence_type == "revision"
        }
        - {None}
    )
    visual_revs = sorted(
        {
            (o.normalized_value or "").strip()
            for o in (visual_observations or [])
            if o.kind == "revision" and o.normalized_value
        }
        - {""}
    )
    revision_domains = {
        "customer_totvs_revision": official_rev or None,
        "engineering_drawing_revision": sorted(set(rev_values)) or None,
        "engineering_drawing_revision_visual": {
            "values": visual_revs or None,
            "provenance": "chatgpt_visual_observation",
            "promoted_to_official": False,
        },
        "drawing_library_revision": (
            str(revision_meta) if revision_meta else None
        ),
        "totvs_vs_drawing_comparable": False,
        "rule": "ENG-REV-001",
    }
    if rev_values or official_rev or revision_meta:
        status, summary = VerificationStatus.PASS, (
            "Domínios de revisão apresentados separadamente — "
            f"cadastro cliente/TOTVS '{official_rev or '—'}' × "
            f"desenho engenharia {sorted(set(rev_values)) or '—'} × "
            f"acervo '{revision_meta or '—'}'. Controles independentes: "
            "diferença de número NÃO é divergência (ENG-REV-001); "
            "comparação só dentro do mesmo domínio."
        )
    else:
        status, summary = VerificationStatus.INCONCLUSIVE, (
            "Nenhuma revisão identificável em qualquer domínio."
        )
    verifications.append(
        Verification(
            key="revision_domains",
            label="Domínios de revisão (ENG-REV-001)",
            status=status,
            summary=summary,
        )
    )

    # V3 — drawing × BOM --------------------------------------------------------
    bom_items: list[dict[str, Any]] = []
    if isinstance(structure, dict):
        # R5.1/S6: raiz implícita = próprio produto analisado quando o
        # nó raiz não carrega `code` (payload real api-delpi).
        _flatten_bom(structure, bom_items, parent_code=code)
    # R5-C/D: estatísticas multinível — ocorrências, códigos, níveis.
    by_type: dict[str, int] = {}
    by_depth: dict[str, int] = {}
    code_occurrences: dict[str, int] = {}
    for item in bom_items:
        t = str(item.get("product_type") or item.get("type") or "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        d = str(item.get("_depth") or "?")
        by_depth[d] = by_depth.get(d, 0) + 1
        c = str(item.get("code") or "")
        if c:
            code_occurrences[c] = code_occurrences.get(c, 0) + 1
    # S6 — semântica explícita de vínculos: raiz→diretos vs aninhados.
    root_child_links = sum(1 for i in bom_items if i.get("_depth") == 1)
    nested_links = sum(
        1 for i in bom_items
        if (i.get("_depth") or 0) > 1 and i.get("_parent_code")
    )
    bom_stats = {
        "total_occurrences": len(bom_items),
        "unique_codes": len(code_occurrences),
        "by_type": by_type,
        "by_depth": by_depth,
        "root_child_links": root_child_links,
        "nested_parent_links": nested_links,
        "total_relationships": root_child_links + nested_links,
        # compat: parent_links = vínculos totais da árvore (inclui raiz).
        "parent_links": sum(1 for i in bom_items if i.get("_parent_code")),
        "direct_children": root_child_links,
        "repeated_codes": {
            c: n for c, n in code_occurrences.items() if n > 1
        },
        "max_depth": max((i.get("_depth") or 0 for i in bom_items), default=0),
    }
    if structure_error is not None:
        verifications.append(
            Verification(
                key="bom_availability",
                label="Disponibilidade da estrutura oficial",
                status=VerificationStatus.INCONCLUSIVE,
                summary=(
                    f"Estrutura não carregada: "
                    f"{structure_error.code} — comparações de BOM "
                    "não executadas."
                ),
            )
        )

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

    # R15/DEC-VAL-022 — diff estrutural por ocorrência: desenho
    # (component_table do understanding visual) × BOM vigente.
    from engineering_app.application.drawing.bom_structure_comparator import (  # noqa: E501
        compare_bom_to_drawing,
    )
    # DEC-VAL-033 evolução — recuperação genérica de células de tabela
    # densa perdidas pelo OCR de página: re-OCR localizado das regiões
    # de tabela (crop vetorial em DPI alto) procura os códigos da BOM
    # sem evidência — presença recuperada entra como token com
    # proveniência `localized_ocr_recheck` (conta presença, nunca
    # fabrica relação). Código esperado nunca é evidência por si só.
    if progressive and drawing_tokens is not None and bom_items:
        from engineering_app.application.drawing.bom_structure_comparator import (  # noqa: E501
            _token_code_set,
        )
        from engineering_app.application.drawing.drawing_investigation import (  # noqa: E501
            recover_absent_table_cells,
        )
        from engineering_app.domain.drawing.object_profiles import (
            is_component_code,
        )

        _ct = (understanding or {}).get("component_table") or {}
        _cell_codes = {
            str(c.get("text") or "").strip()
            for r in _ct.get("rows") or []
            for c in r.get("cells") or []
            if is_component_code(c.get("text"))
        }
        _visible = _cell_codes | _token_code_set(drawing_tokens)
        _missing = [
            str(it.get("component_code") or "").strip()
            for it in bom_items
            if str(it.get("component_code") or "").strip()
            and str(it.get("component_code") or "").strip()
            not in _visible
        ]
        if _missing:
            _recovered = recover_absent_table_cells(
                missing_codes=_missing,
                component_table=_ct,
                opts=progressive,
                tokens=drawing_tokens,
            )
            for _rc in _recovered:
                drawing_tokens.append(
                    {
                        "normalized_text": _rc["code"],
                        "raw_text": _rc["observed_raw_value"],
                        "page": _rc["page"],
                        "confidence": _rc["confidence"],
                        "bounding_box_px": _rc["box"],
                        "provenance": "localized_ocr_recheck",
                    }
                )
                # DEC-VAL-034 — a evidência perceptual deve chegar ao
                # entendimento e à investigação guiada, não só ao
                # comparador: code_contexts (visibilidade estrutural) +
                # localized_recovery (contrato de evidência verificável).
                if isinstance(understanding, dict):
                    _ctx_key = (_rc["code"], "component_table", _rc["page"])
                    _ctxs = understanding.setdefault("code_contexts", [])
                    if not any(
                        (c.get("code"), c.get("region"), c.get("page"))
                        == _ctx_key
                        for c in _ctxs
                    ):
                        _ctxs.append(
                            {
                                "code": _rc["code"],
                                "region": "component_table",
                                "page": _rc["page"],
                                "bounding_box_px": _rc["box"],
                                "provenance": "localized_ocr_recheck",
                                "confidence": _rc["confidence"],
                                "observed_raw_value": (
                                    _rc["observed_raw_value"]
                                ),
                            }
                        )
                    understanding.setdefault(
                        "localized_recovery", []
                    ).append(
                        {
                            "observed_code": _rc["code"],
                            "raw_text": _rc["observed_raw_value"],
                            "product_code": official_code,
                            "pdf_sha256": (
                                getattr(extraction, "document_hash", None)
                                or understanding.get(
                                    "document_hash_sha256"
                                )
                            ),
                            "page": _rc["page"],
                            "region": "component_table",
                            "region_box": _rc.get("region"),
                            "region_ref_dpi": _rc.get("region_ref_dpi"),
                            "bounding_box": _rc["box"],
                            "coordinate_system": (
                                "pixels_pdfium_top_left"
                            ),
                            "method": _rc["method"],
                            "confidence": _rc["confidence"],
                            "source_revision": (
                                str(revision_meta)
                                if revision_meta else None
                            ),
                        }
                    )
    bom_structure_comparison = compare_bom_to_drawing(
        product_code=official_code,
        bom_occurrences=(
            flatten_bom_occurrences(structure, code)
            if isinstance(structure, dict) and structure_error is None
            else None
        ),
        component_table=(
            (understanding or {}).get("component_table")
            if isinstance(understanding, dict)
            else None
        ),
        tokens=drawing_tokens,
        drawing_pages=extraction.page_count,
        code_contexts=(
            (understanding or {}).get("code_contexts")
            if isinstance(understanding, dict)
            else None
        ),
        page_coverage=(
            (understanding or {}).get("page_coverage")
            if isinstance(understanding, dict)
            else None
        ),
        bom_error=(
            {"code": structure_error.code,
             "status_code": structure_error.status_code}
            if structure_error is not None
            else None
        ),
    )
    _bsc_status = bom_structure_comparison["status"]
    verifications.append(
        Verification(
            key="bom_structure_comparison",
            label="Estrutura — desenho × BOM por ocorrência",
            status=(
                VerificationStatus.WARNING
                if _bsc_status == "DIVERGENCES_CANDIDATES"
                else (
                    VerificationStatus.INCONCLUSIVE
                    if _bsc_status == "INCONCLUSIVE"
                    else VerificationStatus.PASS
                )
            ),
            summary=(
                f"{_bsc_status}: "
                f"{bom_structure_comparison['counts'].get('divergences', 0)} "
                "divergência(s) candidata(s) por ocorrência."
            ),
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

    # V4b — quantity semantics (R4: sem conversão inventada) ---------------------
    qty_rows = [
        {
            "code": str(i.get("code") or ""),
            "quantity": i.get("quantity"),
            "unit": str(i.get("unit") or i.get("measure_unit") or ""),
        }
        for i in bom_items
        if i.get("quantity") is not None
    ]
    distinct_units = sorted({r["unit"] for r in qty_rows if r["unit"]})
    verifications.append(
        Verification(
            key="quantity_semantics",
            label="Semântica de quantidades da BOM",
            status=(
                VerificationStatus.INCONCLUSIVE
                if qty_rows
                else VerificationStatus.NOT_APPLICABLE
            ),
            summary=(
                f"{len(qty_rows)} itens com quantidade (unidades fonte: "
                f"{', '.join(distinct_units) or '—'}). Valores são a "
                "representação bruta do SG1 — base de consumo, fator e "
                "unidade secundária não possuem contrato oficial de "
                "conversão: comparação com observações do desenho exige "
                "regra do owner, nunca inferência por magnitude."
                if qty_rows
                else "Sem itens de estrutura com quantidade."
            ),
            evidence_class=EvidenceClass.CALCULATED,
            limitations=[
                "sem contrato de conversão unidade×base de consumo — "
                "643 MT não é presumivelmente 643 m por conjunto; "
                "1000 PC não é presumivelmente consumo por peça"
            ],
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
    reconciliations: list[dict[str, Any]] = []
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
                official_revision=(
                    (revision_domains.get(
                        "engineering_drawing_revision") or [None])[0]
                    or revision_domains.get("drawing_library_revision")
                ),
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

        # --- R5-A: reconciliação de evidências --------------------------------
        def _visual_code_agreement(target_code: str) -> bool:
            for res in visual_results:
                obs = res["observation"]
                for ident in obs.get("identifiers") or []:
                    if ident.get("role") == "product_code" and (
                        ident.get("value") == target_code
                    ):
                        return res["vs_official"]["status"] == "agreement"
                if res["vs_official"]["status"] == "agreement" and (
                    obs.get("kind") == "identification"
                ):
                    return True
            return False

        text_has_code = any(
            e.evidence_type == "code" and e.observed_value == official_code
            for e in evidence
        )
        visual_code_ok = _visual_code_agreement(official_code)
        recon_status = (
            "corroborated" if text_has_code and visual_code_ok
            else "visual_and_official_only" if visual_code_ok
            else "official_only" if text_has_code or official_code
            else "insufficient_evidence"
        )
        reconciliations.append({
            "subject": "product_code",
            "field_role": "product_code",
            "textual_evidence": bool(text_has_code),
            "visual_evidence": bool(visual_code_ok),
            "official_evidence": bool(official_code),
            "reconciliation_status": recon_status,
            "confidence": "high" if visual_code_ok else "medium",
            "limitations": (
                [] if text_has_code else
                ["camada textual não recuperou o código — limitação de "
                 "extração, não evidência de ausência no desenho"]
            ),
            "provenance": ["pypdf_text_layer", "chatgpt_visual",
                           "api_delpi_product"],
        })

        # R5.1: reclassifica findings de ausência textual quando há
        # corroboração visual×oficial (categorias reais: identification/
        # bom — R5 filtrava nomes inexistentes, nunca executava).
        for f in findings:
            diverg = f.divergence or ""
            if "not_located" not in diverg and "without_text" not in diverg:
                continue
            if not _visual_code_agreement(official_code):
                continue
            f.severity = "info"
            f.severity_reason = (
                "Reconciliado: evidência visual concorda com o cadastro "
                "oficial; ausência é limitação da camada textual, não "
                "divergência cadastral."
            )
            f.divergence = "text_coverage_limitation"
            f.recommended_correction = (
                "Sem correção técnica necessária; registrar limitação de "
                "extração textual."
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
            "revision_domains": revision_domains,
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
            "bom_stats": bom_stats,
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
    payload["contract_version"] = "drawing_analysis.v3"
    payload["source_match"] = source_match.value
    payload["visual_observations"] = [
        o.to_dict() for o in visual_observations
    ]
    payload["comparison_results"] = visual_results
    payload["reconciliations"] = reconciliations
    payload["bom_occurrences"] = flatten_bom_occurrences(
        structure if isinstance(structure, dict) else {}, code
    )
    payload["bom_structure_comparison"] = bom_structure_comparison
    payload["scope"] = scope or ["all"]
    if visual_observations:
        payload["executive_summary"]["visual_observations_total"] = len(
            visual_observations
        )
    serialized_verifications = payload["verifications"]
    inconclusive = [
        v for v in serialized_verifications
        if v["status"] in {"INCONCLUSIVE", "NOT_CHECKED", "NOT_APPLICABLE"}
    ]
    serialized_findings = payload["findings"]
    recommendations = [
        {"id": f["id"], "category": f["category"],
         "correction": f["recommended_correction"]}
        for f in serialized_findings
        if f.get("recommended_correction")
    ]
    # R11 — perfis reutilizáveis de objetos (doc 116-B): ocorrências BOM
    # (oficial) + observações visuais (candidato) + relações auditáveis.
    from engineering_app.application.drawing.object_profiles_builder import (
        build_object_profiles,
    )
    payload["object_profiles"] = build_object_profiles(
        bom_occurrences=payload["bom_occurrences"],
        visual_observations=payload["visual_observations"],
        component_rows=None,
        understanding=understanding,
        document_sha=extraction.document_hash,
        official_source_ref=(
            f"api-delpi:/products/{official_code}/structure"
        ),
        official_source_state=(
            "UNAVAILABLE"
            if structure_error is not None
            else ("EMPTY_CONFIRMED" if not bom_items else "AVAILABLE")
        ),
        product_code=official_code,
        progressive=progressive,
        product_revision=official_rev or None,
        include_investigations=True,
    )
    payload["guided_investigations"] = payload["object_profiles"].get(
        "guided_investigations"
    )
    payload["sections"] = {
        "A_identification": payload["identification"],
        "B_executive_summary": payload["executive_summary"],
        "C_visual_checks": [
            v for v in serialized_verifications
            if v["key"] in {
                "legibility", "product_identification", "revision",
                "technical_notes", "units_dimensions", "material_hints",
                "visual_observations", "visual_vs_textual",
            }
        ],
        "D_official_crosschecks": [
            v for v in serialized_verifications
            if v["key"] in {
                "bom_availability", "bom_comparison",
                "bom_structure_comparison", "quantity_semantics",
                "mp_description", "pi_description",
                "mp_items_descriptions", "pi_items_descriptions",
            }
        ],
        "E_findings": serialized_findings,
        "F_inconclusions": inconclusive,
        "G_recommendations": recommendations,
        "H_technical_review": {
            "status": "DRAFT",
            "reviewer": "Engenharia (owner)",
            "human_review_required": True,
            "automatic_approval": False,
        },
    }
    return payload
