"""Guided Drawing Investigation (R12) — a estrutura oficial orienta a
busca; o desenho permanece fonte independente de evidências.

Planner determinístico + executor tipado sobre o mesmo
``DrawingObjectSet`` do R11 — nunca segundo modelo, nunca decisão
arbitrária entre ocorrências repetidas, nunca promoção silenciosa.

Estados: MATCH_CANDIDATE / AMBIGUOUS / NOT_LOCATED / INCONCLUSIVE /
NOT_CHECKED / NOT_COMPARABLE / EXPECTED_COMPONENT_NOT_LOCATED /
UNMATCHED_DRAWING_CANDIDATE.
"""

from __future__ import annotations

from typing import Any

from engineering_app.domain.drawing.object_profiles import (
    ObjectType,
    is_component_code,
)

INVESTIGATION_SCHEMA = "guided_investigations.v1"
_NON_COMPONENT_REGIONS = {"title_block", "revision_history"}
# R12.1 — disponibilidade/comparabilidade da fonte oficial (fail-closed):
OFFICIAL_STATES = frozenset(
    {
        "AVAILABLE",
        "NOT_PROVIDED",
        "UNAVAILABLE",
        "EMPTY_CONFIRMED",
    }
)
_COMPARISON_BLOCKED = {"NOT_PROVIDED", "UNAVAILABLE"}
_REQUIRED_EVIDENCE = ["raw_text", "document_identity", "page", "bounding_box"]


def plan_investigations(oset) -> list[dict[str, Any]]:
    """I-01..I-03: um plano tipado por ocorrência BOM — identidade,
    atributo esperado, fonte oficial e estratégia de busca."""
    plans: list[dict[str, Any]] = []
    for i, occ in enumerate(
        oset.by_type(ObjectType.BOM_OCCURRENCE), start=1
    ):
        a = occ.attributes
        plans.append(
            {
                "investigation_id": f"INV-{i:04d}",
                "expected_object_id": occ.object_id,
                "attribute": "component_code",
                "expected_value": a.get("component_code"),
                "expected_source": occ.document_identity,
                "context": {
                    "parent_code": a.get("parent_code"),
                    "bom_path": a.get("bom_path"),
                    "component_type": a.get("component_type"),
                    "consumption_quantity": a.get("consumption_quantity"),
                    "consumption_unit": a.get("consumption_unit"),
                },
                "search_target": "component_table+identifier_candidates",
                "search_strategy": "EXACT_THEN_CONTEXTUAL",
                "required_evidence": list(_REQUIRED_EVIDENCE),
                "state": "NOT_CHECKED",
            }
        )
    return plans


def _similarity(expected: str, observed: str) -> float:
    """Similaridade posicional simples — nunca comprova correspondência."""
    if not expected or not observed:
        return 0.0
    if len(expected) != len(observed):
        return 0.0
    same = sum(1 for a, b in zip(expected, observed) if a == b)
    return round(same / len(expected), 3)


def _table_candidates(u: dict) -> list[dict]:
    """Linhas da tabela do understanding com código tipado válido."""
    out = []
    for r in ((u.get("component_table") or {}).get("rows") or []):
        f = (r.get("fields") or {}).get("component_code") or {}
        code = r.get("component_code") or f.get("normalized_value")
        out.append(
            {
                "row": r,
                "code": code,
                "fields": r.get("fields") or {},
                "ambiguous": bool(
                    r.get("association_status") != "FIELD_IDENTIFIED"
                    and not r.get("fields")
                )
                or any(c.get("ambiguous") for c in (r.get("cells") or [])),
            }
        )
    return out


def _identifiers_by_region(u: dict) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for f in u.get("identifier_candidates") or []:
        by.setdefault(f.get("region") or "unknown", []).append(f)
    return by


def _evidence_of(candidate: dict) -> list[dict]:
    refs = []
    for name in ("item", "quantity", "component_code", "description"):
        f = candidate["fields"].get(name) or {}
        if f.get("bounding_box_px"):
            refs.append(
                {
                    "source_kind": "drawing_understanding",
                    "raw_value": f.get("raw_text"),
                    "bounding_box": f.get("bounding_box_px"),
                    "coordinate_system": "pixels_pdfium_top_left",
                }
            )
    return refs


def _check_component_code(
    occ, plan, table_rows, idents, document_sha, product_code=None
) -> dict:
    """I-01 — código do componente nas evidências da tabela/OCR."""
    code = plan["expected_value"]
    check = {
        "check": "component_code_in_drawing",
        "state": "NOT_CHECKED",
        "expected_value": code,
        "observed_value": None,
        "candidate_rows": [],
        "uncertainty_reason": None,
        "evidence_refs": [],
    }
    if not code:
        check["state"] = "INCONCLUSIVE"
        check["uncertainty_reason"] = "ocorrência sem código oficial"
        return check
    exact = [c for c in table_rows if c["code"] == code and not c["ambiguous"]]
    amb_rows = [c for c in table_rows if c["code"] == code and c["ambiguous"]]
    if len(exact) > 1:
        check["state"] = "AMBIGUOUS"
        check["observed_value"] = code
        check["candidate_rows"] = [
            {"row": c["row"].get("row"), "reason": "multiple_table_rows"}
            for c in exact
        ]
        check["evidence_refs"] = _evidence_of(exact[0])
        check["uncertainty_reason"] = (
            "mesmo código em múltiplas linhas da tabela — "
            "contexto adicional exigido"
        )
        return check
    if exact:
        check["state"] = "MATCH_CANDIDATE"
        check["observed_value"] = code
        check["candidate_rows"] = [
            {"row": exact[0]["row"].get("row"), "reason": "exact_table_code"}
        ]
        check["evidence_refs"] = _evidence_of(exact[0])
        return check
    if amb_rows:
        check["state"] = "AMBIGUOUS"
        check["observed_value"] = code
        check["candidate_rows"] = [
            {"row": c["row"].get("row"), "reason": "ambiguous_row_association"}
            for c in amb_rows
        ]
        check["uncertainty_reason"] = "linha com associação ambígua"
        return check
    # código presente fora da tabela ≠ evidência de componente
    region_hits = {
        region: [f for f in fs if f.get("text") == code]
        for region, fs in idents.items()
    }
    non_component = [
        region
        for region, fs in region_hits.items()
        if fs and region in _NON_COMPONENT_REGIONS
    ]
    elsewhere = [
        region
        for region, fs in region_hits.items()
        if fs and region not in _NON_COMPONENT_REGIONS
    ]
    similar = [
        {
            "observed_raw_value": f["text"],
            "candidate_similarity": _similarity(code, f["text"]),
            "region": f.get("region"),
        }
        for fs in idents.values()
        for f in fs
        if f.get("text") != code
        and f.get("text") != product_code
        and _similarity(code, f.get("text") or "") >= 0.85
    ]
    if non_component or elsewhere or similar:
        check["state"] = "AMBIGUOUS"
        check["uncertainty_reason"] = "; ".join(
            filter(
                None,
                [
                    "código observado apenas em região não-componente "
                    f"({', '.join(non_component)})"
                    if non_component
                    else None,
                    "código fora da tabela de componentes "
                    f"({', '.join(elsewhere)})"
                    if elsewhere
                    else None,
                    "candidatos similares sem prova de correspondência"
                    if similar
                    else None,
                ],
            )
        )
        check["similar_candidates"] = similar[:5]
        return check
    check["state"] = "NOT_LOCATED"
    check["uncertainty_reason"] = (
        "não identificado nas evidências analisadas — ausência de "
        "leitura não é ausência física"
    )
    return check


def _check_row_attributes(candidate: dict | None) -> dict:
    """I-02 — atributos da linha: item, quantidade de montagem, descrição."""
    check = {
        "check": "table_item_attributes",
        "state": "NOT_CHECKED",
        "observed": {},
        "uncertainty_reason": None,
    }
    if not candidate:
        check["uncertainty_reason"] = "sem linha candidata"
        return check
    fields = candidate["fields"]
    qty = (fields.get("quantity") or {}).get("normalized_value")
    item = (fields.get("item") or {}).get("normalized_value")
    observed = {
        "item_label": item or candidate["row"].get("item"),
        "assembly_quantity": qty or candidate["row"].get("quantity"),
        "description": candidate["row"].get("description"),
    }
    check["observed"] = observed
    ambiguous_qty = bool(qty) and not str(qty).replace(",", ".").replace(
        ".", "", 1
    ).isdigit()
    merged = any(
        (c or {}).get("ambiguous") for c in (candidate["row"].get("cells") or [])
    )
    if ambiguous_qty or merged or candidate["ambiguous"]:
        check["state"] = "AMBIGUOUS"
        reasons = []
        if ambiguous_qty:
            reasons.append("assembly_quantity_not_numeric")
            observed["assembly_quantity_raw"] = qty
            observed["assembly_quantity"] = None
        if merged or candidate["ambiguous"]:
            reasons.append("table_field_alignment_unresolved")
        check["uncertainty_reason"] = "; ".join(reasons)
        return check
    check["state"] = "MATCH_CANDIDATE"
    return check


def _check_relations(occ, oset) -> dict:
    """I-03 — relações candidatas já compostas no mesmo conjunto."""
    rels = [
        r
        for r in oset.relations()
        if r.source_object_id == occ.object_id
        or r.target_object_id == occ.object_id
    ]
    return {
        "check": "bom_occurrence_relation",
        "state": "MATCH_CANDIDATE" if rels else "NOT_LOCATED",
        "relation_count": len(rels),
        "relation_refs": [
            {
                "relation_type": r.relation_type.value,
                "target_object_id": r.target_object_id,
                "verification_state": r.verification_state.value,
                "uncertainty_reason": r.uncertainty_reason,
            }
            for r in rels
        ],
        "uncertainty_reason": (
            "todas as ocorrências do mesmo código permanecem "
            "candidatas — nenhuma escolhida arbitrariamente"
            if rels
            else "sem evidência de associação"
        ),
    }


def _y_band(cells: list[dict], y: float, tol: float = 12.0) -> list[dict]:
    """Agrupa células na mesma faixa vertical (linha física)."""
    def _cy(c):
        box = c.get("bounding_box_px") or []
        return (box[1] + (box[5] if len(box) > 5 else box[1])) / 2 if box else 0
    return [c for c in cells if abs(_cy(c) - y) <= tol]


def _contextual_search(plan: dict, u: dict) -> dict:
    """Etapa 2 (R13): procura o código esperado nas células brutas da
    tabela e tenta re-associação espacial de linha — sem promover."""
    code = plan["expected_value"]
    out = {
        "stage": "CONTEXTUAL_SEARCH",
        "result": "NO_CANDIDATE_REGION",
        "candidate_rows": [],
        "observations": [],
    }
    if not code:
        return out
    hits = []
    for r in ((u.get("component_table") or {}).get("rows") or []):
        for c in r.get("cells") or []:
            t = (c.get("text") or "").strip()
            if t == code:
                hits.append({"row": r, "cell": c, "similarity": 1.0})
            elif _similarity(code, t) >= 0.85:
                hits.append({"row": r, "cell": c, "similarity": _similarity(code, t)})
    if not hits:
        return out
    exact = [h for h in hits if h["similarity"] >= 1.0]
    out["observations"] = [
        {
            "observed_raw_value": h["cell"].get("text"),
            "candidate_similarity": h["similarity"],
            "bounding_box": h["cell"].get("bounding_box_px"),
            "coordinate_system": "pixels_pdfium_top_left",
        }
        for h in hits[:10]
    ]
    if not exact:
        out["result"] = "SIMILAR_ONLY"
        out["candidate_rows"] = [
            {"row": h["row"].get("row"), "reason": "similar_not_equal"}
            for h in hits
        ]
        return out
    # re-associação espacial: linha física → campos lógicos
    for h in exact[:4]:
        band = _y_band(
            h["row"].get("cells") or [],
            ((h["cell"].get("bounding_box_px") or [0, 0])[1]),
        )
        out["candidate_rows"].append(
            {
                "row": h["row"].get("row"),
                "reason": "code_in_raw_cell",
                "cells_in_band": len(band),
            }
        )
    out["result"] = (
        "ROW_ASSOCIATION_CANDIDATE" if len(exact) == 1
        else "ROW_ASSOCIATION_AMBIGUOUS"
    )
    return out


def _targeted_recheck(plan: dict, region_box, opts: dict) -> dict:
    """Etapa 3 (R13): recorte direcionado + OCR localizado via ports —
    somente quando evidência existente é insuficiente."""
    hist = {"stage": "TARGETED_RECHECK", "result": "NOT_ATTEMPTED",
            "observations": []}
    renderer = opts.get("renderer")
    ocr = opts.get("ocr")
    pdf_bytes = opts.get("pdf_bytes")
    budget = opts.get("budget") or {}
    state = opts.setdefault("state", {"crops": 0})
    if not all([renderer, ocr, pdf_bytes, region_box]):
        hist["result"] = "CAPABILITY_UNAVAILABLE"
        return hist
    if state["crops"] >= int(budget.get("max_crops", 8)):
        hist["result"] = "RESOURCE_LIMIT_REACHED"
        return hist
    state["crops"] += 1
    try:
        region = renderer.render_region(
            pdf_bytes,
            page=int(opts.get("page") or 1),
            region_px=region_box,
            reference_dpi=int(opts.get("reference_dpi") or 150),
            dpi=min(int(budget.get("max_dpi", 300)), 300),
            margin_px=8,
        )
        if region.width * region.height > int(
            budget.get("max_pixels", 4_000_000)
        ):
            hist["result"] = "RESOURCE_LIMIT_REACHED"
            return hist
        res = ocr.extract_text(region.image_bytes)
        code = plan["expected_value"]
        found = [
            {
                "observed_raw_value": t.text,
                "candidate_similarity": _similarity(code, t.text or ""),
                "method": "localized_ocr_recheck",
                "page": region.page,
            }
            for t in (res.tokens or [])
            if t.text and (t.text == code or _similarity(code, t.text) >= 0.85)
        ]
        hist["observations"] = found
        hist["result"] = (
            "CODE_OBSERVED" if any(
                f["observed_raw_value"] == code for f in found
            )
            else ("SIMILAR_ONLY" if found else "CODE_NOT_FOUND")
        )
    except Exception as exc:  # provider/timeout/OOM — estado honesto
        hist["result"] = "PROVIDER_ERROR"
        hist["detail"] = type(exc).__name__
    return hist


def identify_balloon_candidates(u: dict) -> list[dict]:
    """R13 — primeira capacidade genérica de balões: token alfanumérico
    curto contido em primitiva circular/elíptica. Nunca fabrica balões."""
    prims = u.get("graphic_primitives") or []
    circles = [
        p for p in prims
        if (p.get("type") or "").lower() in {"circle", "ellipse", "arc"}
    ]
    if not circles:
        return []
    toks = u.get("_tokens") or u.get("tokens") or []
    out = []
    def _bounds(box):
        xs = box[0::2]
        ys = box[1::2]
        return min(xs), min(ys), max(xs), max(ys)

    def _inside(tb, cb):
        if len(tb) < 4 or len(cb) < 4:
            return False
        tx1, ty1, tx2, ty2 = _bounds(tb)
        cx1, cy1, cx2, cy2 = _bounds(cb)
        return (
            cx1 <= tx1 and cx2 >= tx2 and cy1 <= ty1 and cy2 >= ty2
        )
    for circ in circles:
        cbox = circ.get("bounding_box_px") or circ.get("box_px") or []
        for t in toks:
            txt = (t.get("normalized_text") or t.get("text") or "").strip()
            tbox = t.get("bounding_box_px") or []
            if 1 <= len(txt) <= 3 and txt.isalnum() and _inside(tbox, cbox):
                out.append(
                    {
                        "item_label": txt,
                        "bounding_box_px": cbox,
                        "token_bounding_box_px": tbox,
                        "region": t.get("region"),
                        "identification_method": "primitive_containment",
                        "uncertainty_reason": "contenção geométrica é "
                        "candidata — exige verificação visual",
                    }
                )
    return out


def _checks_by_state(results: list[dict]) -> dict[str, int]:
    """Contagem global por estado de check — consolidação auditável."""
    counts: dict[str, int] = {}
    for r in results:
        for c in r.get("investigations") or []:
            s = str(c.get("state") or "NOT_CHECKED")
            counts[s] = counts.get(s, 0) + 1
    return counts


def _global_state(results: list[dict], comparison_blocked: bool) -> str:
    """Estado global honesto — nunca PASS; consolidação por cobertura."""
    if comparison_blocked:
        return "INCONCLUSIVE"
    if not results:
        return "INCONCLUSIVE"
    states = {r.get("overall_state") for r in results}
    if "NOT_COMPARABLE" in states and len(states) == 1:
        return "NOT_COMPARABLE"
    if states <= {"MATCH_CANDIDATE"}:
        return "MATCH_CANDIDATE"
    return "INCONCLUSIVE"


def execute_investigations(
    oset,
    plans: list[dict],
    understanding: dict | None,
    *,
    document_sha: str | None,
    official_source_state: str | None = None,
    product_code: str | None = None,
    progressive: dict | None = None,
) -> dict[str, Any]:
    """Executor I-01..I-05 sobre o mesmo DrawingObjectSet.

    ``official_source_state`` declara a disponibilidade da estrutura
    oficial: AVAILABLE | NOT_PROVIDED | UNAVAILABLE | EMPTY_CONFIRMED.
    Sem BOM oficial (NOT_PROVIDED/UNAVAILABLE) a comparação é fail-closed:
    nenhum UNMATCHED_DRAWING_CANDIDATE pode ser afirmado.
    """
    u = understanding or {}
    if official_source_state is None:
        official_source_state = (
            "AVAILABLE"
            if oset.by_type(ObjectType.BOM_OCCURRENCE)
            else "NOT_PROVIDED"
        )
    comparison_blocked = official_source_state in _COMPARISON_BLOCKED
    u_doc = u.get("document_hash_sha256")
    identity_conflict = bool(
        document_sha and u_doc and document_sha != u_doc
    )
    if comparison_blocked:
        limitations = [
            "OFFICIAL_COMPARISON_NOT_EXECUTED — fonte oficial "
            f"{official_source_state}: observações visuais preservadas "
            "como candidatas, nunca classificadas como divergentes ou "
            "sem correspondência oficial",
            "ausência de BOM não é BOM vazia — cobertura nula por "
            "impossibilidade de comparação",
        ]
        return {
            "schema_version": INVESTIGATION_SCHEMA,
            "official_source_state": official_source_state,
            "document_identity": {
                "set_document_sha": document_sha,
                "understanding_document_sha": u_doc,
                "match": (
                    None
                    if not (document_sha and u_doc)
                    else not identity_conflict
                ),
            },
            "plan": plans,
            "occurrence_results": [],
            "unmatched_drawing_candidates": [],
            "summary": {
                "expected_occurrences": 0,
                "investigations_executed": 0,
                "match_candidates": 0,
                "ambiguous": 0,
                "not_located": 0,
                "not_comparable": 0,
                "not_checked": 0,
                "unmatched_drawing_candidates": 0,
                "effective_coverage": None,
            },
            "limitations": limitations,
            "state": "DRAFT/CANDIDATE",
            "not_official": True,
            "human_review_required": True,
        }
    table_rows = _table_candidates(u)
    idents = _identifiers_by_region(u)
    bom_codes = {
        o.attributes.get("component_code")
        for o in oset.by_type(ObjectType.BOM_OCCURRENCE)
    }
    item_by_row = {
        o.attributes.get("row"): o for o in oset.by_type(
            ObjectType.DRAWING_TABLE_ITEM
        )
    }

    results: list[dict] = []
    totals = {
        "expected_occurrences": len(plans),
        "investigations_executed": 0,
        "match_candidates": 0,
        "ambiguous": 0,
        "not_located": 0,
        "not_comparable": 0,
        "not_checked": 0,
    }
    for occ, plan in zip(oset.by_type(ObjectType.BOM_OCCURRENCE), plans):
        checks = []
        if identity_conflict:
            for key in (
                "component_code_in_drawing",
                "table_item_attributes",
                "bom_occurrence_relation",
            ):
                checks.append(
                    {
                        "check": key,
                        "state": "NOT_COMPARABLE",
                        "uncertainty_reason": (
                            "documento visual incompatível com a fonte — "
                            "fail-closed"
                        ),
                    }
                )
            results.append(
                {
                    "occurrence_id": occ.object_id,
                    "component_code": plan["expected_value"],
                    "investigations": checks,
                    "overall_state": "NOT_COMPARABLE",
                }
            )
            totals["not_comparable"] += 1
            continue
        c1 = _check_component_code(
            occ, plan, table_rows, idents, document_sha, product_code
        )
        checks.append(c1)
        row_ref = None
        if c1["state"] in {"MATCH_CANDIDATE", "AMBIGUOUS"} and c1.get(
            "candidate_rows"
        ):
            rnum = c1["candidate_rows"][0].get("row")
            row_ref = next(
                (c for c in table_rows if c["row"].get("row") == rnum),
                None,
            )
        checks.append(_check_row_attributes(row_ref))
        checks.append(_check_relations(occ, oset))
        checks.append(
            {
                "check": "balloon_relation",
                "state": "NOT_CHECKED",
                "reason": "balloon_detection_unavailable"
                if not oset.by_type(ObjectType.BALLOON)
                else "pending_verification",
            }
        )
        checks.append(
            {
                "check": "dimension_relation",
                "state": "NOT_CHECKED",
                "reason": "geometry_association_unavailable"
                if not oset.by_type(ObjectType.DRAWING_GEOMETRY)
                else "pending_verification",
            }
        )
        if c1["state"] == "NOT_LOCATED":
            overall = "EXPECTED_COMPONENT_NOT_LOCATED"
        elif c1["state"] == "AMBIGUOUS":
            overall = "INCONCLUSIVE"
        elif c1["state"] == "MATCH_CANDIDATE":
            overall = "MATCH_CANDIDATE"
        else:
            overall = "INCONCLUSIVE"
        results.append(
            {
                "occurrence_id": occ.object_id,
                "component_code": plan["expected_value"],
                "investigations": checks,
                "overall_state": overall,
            }
        )
        totals["investigations_executed"] += 1
        if c1["state"] == "MATCH_CANDIDATE":
            totals["match_candidates"] += 1
        elif c1["state"] == "AMBIGUOUS":
            totals["ambiguous"] += 1
        elif c1["state"] == "NOT_LOCATED":
            totals["not_located"] += 1
        else:
            totals["not_checked"] += 1

    # R13 — investigação visual progressiva sobre ocorrências sem
    # resolução: EXISTING_EVIDENCE → CONTEXTUAL_SEARCH → TARGETED_RECHECK
    # (ports, budget governado). Histórico de busca ≠ evidência técnica.
    balloon_candidates: list[dict] = []
    if progressive:
        rows_all = (u.get("component_table") or {}).get("rows") or []
        for res, plan in zip(results, plans):
            if res["overall_state"] not in {
                "INCONCLUSIVE", "EXPECTED_COMPONENT_NOT_LOCATED",
                "AMBIGUOUS",
            }:
                continue
            hist = [
                {"stage": "EXISTING_EVIDENCE",
                 "result": res["overall_state"]}
            ]
            ctx = _contextual_search(plan, u)
            hist.append(ctx)
            recheck = None
            if ctx["result"] != "NO_CANDIDATE_REGION":
                box = None
                if ctx["candidate_rows"]:
                    rn = ctx["candidate_rows"][0].get("row")
                    row = next(
                        (r for r in rows_all if r.get("row") == rn), None
                    )
                    if row:
                        boxes = [
                            c["bounding_box_px"]
                            for c in row.get("cells") or []
                            if c.get("bounding_box_px")
                        ]
                        if boxes:
                            box = [
                                min(b[0] for b in boxes),
                                min(b[1] for b in boxes),
                                max(b[2] for b in boxes),
                                max(b[5] if len(b) > 5 else b[3] for b in boxes),
                            ]
                recheck = _targeted_recheck(plan, box, progressive)
                hist.append(recheck)
            res["search_history"] = hist
            if recheck and recheck.get("result") == "CODE_OBSERVED":
                res["overall_state"] = "MATCH_CANDIDATE"
            elif ctx["result"] == "ROW_ASSOCIATION_CANDIDATE":
                res["overall_state"] = "INCONCLUSIVE"
        balloon_candidates = identify_balloon_candidates(u)

    if not balloon_candidates:
        balloon_candidates = [
            {
                "item_label": b.attributes.get("item_label"),
                "bounding_box_px": (
                    (b.evidence_refs[0].bounding_box
                     if b.evidence_refs else None)
                ),
                "identification_method": b.attributes.get(
                    "identification_method", "declared"
                ),
            }
            for b in oset.by_type(ObjectType.BALLOON)
        ]

    # I-05 — reconciliação independente: desenho → estrutura oficial.
    # R13-01: o identificador do produto raiz NÃO é componente extra.
    root_ids = {str(product_code or "").strip()} - {""}
    unmatched = []
    root_identifiers = []
    for c in table_rows:
        code = c["code"]
        if not code or code in bom_codes:
            continue
        if code in root_ids or not is_component_code(code):
            root_identifiers.append(
                {
                    "identifier_type": "ROOT_PRODUCT_IDENTIFIER"
                    if code in root_ids
                    else "DRAWING_COMPONENT_CANDIDATE",
                    "observed_raw_value": code,
                    "state": "IDENTIFIED_NOT_BOM_COMPONENT"
                    if code in root_ids
                    else "SKIPPED",
                }
            )
            continue
        unmatched.append(
            {
                "candidate_type": "drawing_table_item",
                "observed_raw_value": code,
                "state": "UNMATCHED_DRAWING_CANDIDATE",
                "reason": "sem correspondente oficial — não é prova "
                "de componente extra nem erro de BOM",
            }
        )
    for region, fs in idents.items():
        if region in _NON_COMPONENT_REGIONS:
            continue
        for f in fs:
            t = f.get("text")
            if not t or t in bom_codes:
                continue
            if t in root_ids:
                root_identifiers.append(
                    {
                        "identifier_type": "ROOT_PRODUCT_IDENTIFIER",
                        "observed_raw_value": t,
                        "region": region,
                        "state": "IDENTIFIED_NOT_BOM_COMPONENT",
                    }
                )
                continue
            unmatched.append(
                {
                    "candidate_type": "identifier",
                    "observed_raw_value": t,
                    "region": region,
                    "state": "UNMATCHED_DRAWING_CANDIDATE",
                    "reason": "identificador sem correspondente oficial",
                }
            )

    return {
        "schema_version": INVESTIGATION_SCHEMA,
        "official_source_state": official_source_state,
        "document_identity": {
            "set_document_sha": document_sha,
            "understanding_document_sha": u_doc,
            "match": (
                None
                if not (document_sha and u_doc)
                else not identity_conflict
            ),
        },
        "plan": plans,
        "occurrence_results": results,
        "unmatched_drawing_candidates": unmatched,
        "root_product_identifiers": root_identifiers,
        "balloon_candidates": balloon_candidates,
        "summary": {
            **totals,
            "unmatched_drawing_candidates": len(unmatched),
            "root_product_identifiers": len(root_identifiers),
            "balloon_candidates": len(balloon_candidates),
            "checks_by_state": _checks_by_state(results),
            "global_state": _global_state(results, comparison_blocked),
            "effective_coverage": (
                round(
                    totals["match_candidates"] / totals["expected_occurrences"], 3
                )
                if totals["expected_occurrences"]
                else None
            ),
        },
        "limitations": [
            "MATCH_CANDIDATE não é aprovação técnica — candidato auditável",
            "ausência de leitura não é ausência física no desenho",
            "similaridade não comprova correspondência",
            "consumo×montagem×cota não comparáveis sem regra oficial",
            "cobertura depende das evidências do Drawing Understanding",
        ],
        "state": "DRAFT/CANDIDATE",
        "not_official": True,
        "human_review_required": True,
    }
