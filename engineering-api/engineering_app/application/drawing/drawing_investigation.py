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

import math
from typing import Any

from engineering_app.application.drawing.bom_structure_comparator import (
    _token_code_set,
)
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
    occ, plan, table_rows, idents, document_sha, product_code=None,
    recovery=None,
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
    # DEC-VAL-034 — evidência produzida por recuperação localizada
    # dentro da faixa da tabela de componentes conta como observação
    # estrutural: o crop é delimitado pela própria tabela tipada
    # (faixa y) expandida por tokens na faixa — não é token solto.
    rec_hits = [
        r for r in (recovery or [])
        if r.get("observed_code") == code
    ]
    if len(rec_hits) == 1:
        r = rec_hits[0]
        check["state"] = "MATCH_CANDIDATE"
        check["observed_value"] = r.get("raw_text") or code
        check["candidate_rows"] = [
            {
                "row": None,
                "reason": "localized_ocr_recheck",
                "page": r.get("page"),
            }
        ]
        check["evidence_refs"] = [
            {
                "source_kind": "localized_ocr_recheck",
                "raw_value": r.get("raw_text"),
                "bounding_box": r.get("bounding_box"),
                "coordinate_system": "pixels_pdfium_top_left",
                "page": r.get("page"),
                "region": r.get("region"),
                "region_box": r.get("region_box"),
                "region_ref_dpi": r.get("region_ref_dpi"),
                "method": r.get("method"),
                "confidence": r.get("confidence"),
                "document_sha256": r.get("pdf_sha256"),
                "source_revision": r.get("source_revision"),
            }
        ]
        return check
    if len(rec_hits) > 1:
        check["state"] = "AMBIGUOUS"
        check["observed_value"] = code
        check["candidate_rows"] = [
            {"row": None, "reason": "multiple_recovery_hits",
             "page": r.get("page")}
            for r in rec_hits
        ]
        check["uncertainty_reason"] = (
            "código recuperado em múltiplas regiões localizadas"
        )
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


def _targeted_recheck(plan: dict, region_box, opts: dict,
                      page: int | None = None) -> dict:
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
    page_no = int(page or opts.get("page") or 1)
    ref_dpi = int(
        (opts.get("reference_dpi_by_page") or {}).get(page_no)
        or opts.get("reference_dpi") or 150
    )
    try:
        region = renderer.render_region(
            pdf_bytes,
            page=page_no,
            region_px=region_box,
            reference_dpi=ref_dpi,
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


def _acceptance_matrix(comparison_blocked: bool) -> dict:
    """Matriz consolidada M0–M4 por evidência real (M5) — honesta."""
    return {
        "M0_evaluation_foundation": {
            "state": "BLOCKED",
            "evidence": "sem GT aprovado por owner nem thresholds oficiais",
            "owner": "Engineering/Engenharia",
        },
        "M1_document_structure": {
            "state": "PARTIAL",
            "evidence": "regiões/tabela/topologia SLANet implementadas; "
            "acurácia contra GT não medida",
        },
        "M2_typed_semantic_extraction": {
            "state": "PARTIAL",
            "evidence": "campos tipados item/qty/código/descrição extraídos; "
            "precisão/recall não medidos sem GT",
        },
        "M3_technical_geometric": {
            "state": "PARTIAL",
            "evidence": "cotas/geometria candidatas + recorte direcionado; "
            "balões limitados a primitivas circulares; precisão pendente",
        },
        "M4_governed_cross_check": {
            "state": "PROVEN_STRUCTURE",
            "evidence": "multiplicity-aware + attribute verifications + "
            "divergências versionadas executando em prod",
        },
        "M5_release": {
            "state": "PENDING",
            "evidence": "pacote de revisão entregue; decisão do owner",
        },
        "blocked_because": (
            "official_source_blocked" if comparison_blocked else None
        ),
    }


def _divergence_cards(divergences: list[dict]) -> list[dict]:
    """Cartões legíveis por divergência candidata — todos os campos
    exigidos pelo M5; gravidade somente com classificação autorizada."""
    return [
        {
            **d,
            "next_action": "revisão técnica humana — contexto adicional "
            "exigido para pareamento",
            "severity": None,
            "severity_reason": "sem classificação técnica autorizada",
        }
        for d in divergences
    ]


def build_release_consolidation(
    oset,
    *,
    document_sha: str | None,
    product_revision: str | None,
    occurrence_results: list[dict],
    cross_check: dict,
    comparison_blocked: bool,
) -> dict:
    """M5 — consolidação de produto: FATO_OFICIAL × OBSERVAÇÃO × HIPÓTESE
    × VERIFICAÇÃO por componente, divergência-cards, pacote de revisão
    humana e matriz de aceite. Nunca publica nem aprova."""
    components = []
    verifs = cross_check.get("attribute_verifications") or []
    ver_by_occ: dict[str, list[dict]] = {}
    for v in verifs:
        ver_by_occ.setdefault(str(v.get("expected_object_id")), []).append(v)
    res_by_occ = {
        r.get("occurrence_id"): r for r in (occurrence_results or [])
    }
    for o in oset.by_type(ObjectType.BOM_OCCURRENCE):
        oid = o.object_id
        res = res_by_occ.get(oid) or {}
        components.append(
            {
                "occurrence_id": oid,
                "official": {
                    "component_code": o.attributes.get("component_code"),
                    "component_type": o.attributes.get("component_type"),
                    "parent_code": o.attributes.get("parent_code"),
                    "consumption_quantity": o.attributes.get(
                        "consumption_quantity"
                    ),
                    "consumption_unit": o.attributes.get("consumption_unit"),
                    "component_description": o.attributes.get(
                        "component_description"
                    ),
                    "source": o.document_identity,
                    "class": "FATO_OFICIAL",
                },
                "observed": {
                    "overall_state": res.get("overall_state"),
                    "class": "OBSERVAÇÃO",
                },
                "hypotheses": {
                    "relations": (res.get("investigations") or [{}, {}, {}])[2]
                    .get("relation_refs", []),
                    "class": "HIPÓTESE",
                },
                "verifications": {
                    "checks": ver_by_occ.get(oid, []),
                    "class": "VERIFICAÇÃO",
                },
                "next_action": (
                    "revisão técnica"
                    if res.get("overall_state") != "MATCH_CANDIDATE"
                    else "revisão humana de candidato — não aprovação"
                ),
            }
        )
    return {
        "components": components,
        "divergence_cards": _divergence_cards(
            cross_check.get("candidate_divergences") or []
        ),
        "review_package": {
            "state": "PENDING_OWNER_REVIEW",
            "owner": "Engenharia (Portal Engenharia)",
            "items": len(components),
            "automatic_approval": False,
            "dependency": "workflow oficial de revisão inexistente — "
            "evidências preparadas, decisão permanece no owner",
        },
        "acceptance_matrix": _acceptance_matrix(comparison_blocked),
        "state": "DRAFT/CANDIDATE",
        "not_official": True,
        "human_review_required": True,
    }


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


def _contract_matrix() -> dict:
    """Matriz de contratos oficiais (M4) — inventário estático de
    fontes, owners e regras de comparabilidade autorizadas."""
    return {
        "sources": [
            {
                "name": "product.detail",
                "owner": "api-delpi (Domain API)",
                "access": "delegated_user backend-first, fail-closed",
                "freshness": "live call",
                "errors": "typed 502 source_unavailable — nunca mascarado",
            },
            {
                "name": "product.structure",
                "owner": "api-delpi (Domain API)",
                "access": "delegated_user backend-first",
                "freshness": "live call",
                "errors": "typed — UNAVAILABLE distinto de EMPTY_CONFIRMED",
            },
            {
                "name": "product.drawing_pdf",
                "owner": "fileserver/DELPI (PDF oficial)",
                "identity": "document_hash_sha256 + revision quando presente",
                "errors": "page_out_of_bounds / provider_unavailable tipados",
            },
            {
                "name": "drawing_understanding",
                "owner": "Engineering API (evidência visual candidata)",
                "nature": "observação — nunca fato oficial",
            },
        ],
        "comparability_rules": [
            {"attribute": "component_code", "rule": "EXACT_OBSERVED"},
            {"attribute": "assembly_quantity vs consumption_quantity",
             "rule": "NOT_COMPARABLE — conceitos distintos"},
            {"attribute": "drawing_dimension vs quantity",
             "rule": "NOT_COMPARABLE — naturezas distintas"},
            {"attribute": "revision(TOTVS) vs revision(desenho)",
             "rule": "NOT_COMPARABLE — domínios distintos (ENG-REV-001)"},
            {"attribute": "raw units MT/MI/PC/etc",
             "rule": "PENDING_RULE_VALIDATION — sem contrato de unidades"},
            {"attribute": "item_label/description",
             "rule": "NOT_CHECKED — sem correspondente oficial tipado"},
        ],
    }


def _attr(component, attribute, expected, observed, state, reason,
          evidence=None, observed_raw=None):
    return {
        "attribute": attribute,
        "expected_object_id": component,
        "expected_value": expected,
        "observed_value": observed,
        "observed_raw_value": observed_raw if observed_raw is not None
        else observed,
        "state": state,
        "reason": reason,
        "evidence_refs": evidence or [],
    }


def build_official_cross_check(
    oset,
    plans: list[dict],
    understanding: dict | None,
    *,
    document_sha: str | None,
    product_code: str | None = None,
    product_revision: str | None = None,
    occurrence_results: list[dict] | None = None,
) -> dict:
    """M4 — reconciliação técnica governada oficial × desenho.

    Multiplicity-aware: ocorrências repetidas preservam identidades;
    MATCH/CONFLICT somente com evidência e contrato; ausência de leitura
    nunca é divergência. Comparação bidirecional versionada."""
    u = understanding or {}
    occs = oset.by_type(ObjectType.BOM_OCCURRENCE)
    items = oset.by_type(ObjectType.DRAWING_TABLE_ITEM)
    code_of_occ = {
        o.object_id: o.attributes.get("component_code") for o in occs
    }

    # --- multiplicidade: occurrences × table rows por código -----------
    rows_by_code: dict[str, list[str]] = {}
    for it in items:
        code = it.attributes.get("component_code_candidate")
        if code and not it.attributes.get("ambiguities"):
            rows_by_code.setdefault(code, []).append(it.object_id)
    occ_by_code: dict[str, list[str]] = {}
    for o in occs:
        occ_by_code.setdefault(
            str(o.attributes.get("component_code") or ""), []
        ).append(o.object_id)
    multiplicity = {}
    for code, oids in occ_by_code.items():
        rows = rows_by_code.get(code, [])
        n_o, n_r = len(oids), len(rows)
        pairing = (
            "SINGLE_PAIR" if n_o == 1 and n_r == 1
            else "MANY_TO_ONE" if n_o > 1 and n_r == 1
            else "MANY_TO_MANY" if n_o > 1 and n_r > 1
            else "ONE_TO_NONE" if n_r == 0
            else "PAIR_AMBIGUOUS"
        )
        multiplicity[code] = {
            "bom_occurrence_ids": oids,
            "drawing_item_ids": rows,
            "pairing": pairing,
        }

    # --- verificação por atributo --------------------------------------
    verifications: list[dict] = []
    results_by_occ = {
        r["occurrence_id"]: r for r in (occurrence_results or [])
    }
    for o in occs:
        oid = o.object_id
        code = code_of_occ.get(oid)
        res = results_by_occ.get(oid) or {}
        inv0 = (res.get("investigations") or [{}])[0]
        st = inv0.get("state")
        code_state = (
            "MATCH" if st == "MATCH_CANDIDATE"
            else "NOT_CHECKED" if st == "NOT_CHECKED"
            else "UNKNOWN"
        )
        verifications.append(_attr(
            oid, "component_code", code,
            inv0.get("observed_value"), code_state,
            "observação exata" if code_state == "MATCH"
            else "candidata/ambígua/ausente — nunca confirmada",
            evidence=inv0.get("evidence_refs"),
        ))
        verifications.append(_attr(
            oid, "assembly_quantity",
            o.attributes.get("consumption_quantity"),
            (res.get("investigations") or [{}, {}])[1].get(
                "observed", {}
            ).get("assembly_quantity"),
            "NOT_COMPARABLE",
            "consumo_BOM ≠ quantidade_montagem — conceitos distintos",
        ))
        verifications.append(_attr(
            oid, "component_type",
            o.attributes.get("component_type"),
            None, "NOT_CHECKED",
            "sem campo tipado correspondente no desenho",
        ))
        expected_desc = o.attributes.get("component_description")
        observed_desc = (res.get("investigations") or [{}, {}])[1].get(
            "observed", {}
        ).get("description")
        if expected_desc and observed_desc:
            same = (
                " ".join(str(expected_desc).split()).casefold()
                == " ".join(str(observed_desc).split()).casefold()
            )
            desc_state = "MATCH_CANDIDATE" if same else "CONFLICT_CANDIDATE"
            desc_reason = (
                "igualdade literal normalizada — sem política semântica "
                "aprovada; não é aprovação"
                if same
                else "textos diferem; equivalência semântica OWNER_BLOCKED "
                "— candidato, não NC"
            )
        else:
            desc_state = "NOT_CHECKED"
            desc_reason = (
                "descrição ausente em um dos lados — ausência de texto "
                "não é divergência"
            )
        verifications.append(_attr(
            oid, "description",
            expected_desc, observed_desc, desc_state, desc_reason,
        ))

    # --- revisão: domínios distintos → NOT_COMPARABLE ------------------
    rev_candidates = u.get("revision_candidates") or []
    verifications.append(_attr(
        "product", "revision",
        product_revision,
        rev_candidates[0].get("revision") if rev_candidates else None,
        "NOT_COMPARABLE" if (product_revision and rev_candidates)
        else "NOT_CHECKED",
        "domínios de revisão distintos (TOTVS≠desenho) — ENG-REV-001"
        if product_revision
        else "revisão oficial não consultada neste fluxo",
    ))

    # --- divergências candidatas versionadas ---------------------------
    divergences: list[dict] = []
    for code, m in multiplicity.items():
        if m["pairing"] in {"MANY_TO_ONE", "MANY_TO_MANY", "PAIR_AMBIGUOUS"}:
            divergences.append({
                "divergence_type": "MULTIPLICITY_AMBIGUITY",
                "component_code": code,
                "official_value": m["bom_occurrence_ids"],
                "observed_value": m["drawing_item_ids"],
                "object_refs": m["bom_occurrence_ids"] + m["drawing_item_ids"],
                "document_sha": document_sha,
                "policy": "multiplicity-aware — nenhuma escolha arbitrária",
                "state": "UNKNOWN",
                "reason": "ocorrências/linhas repetidas sem contexto "
                "adicional para pareamento único",
            })
    return {
        "contract_matrix": _contract_matrix(),
        "multiplicity_analysis": multiplicity,
        "attribute_verifications": verifications,
        "candidate_divergences": divergences,
        "bidirectional": {
            "bom_to_drawing": "occurrence_results",
            "drawing_to_bom": "unmatched_drawing_candidates + "
            "root_product_identifiers",
            "note": "ausência de leitura/OCR ambíguo/relação não "
            "verificada ≠ divergência confirmada",
        },
        "state": "DRAFT/CANDIDATE",
        "not_official": True,
        "human_review_required": True,
    }


def execute_investigations(
    oset,
    plans: list[dict],
    understanding: dict | None,
    *,
    document_sha: str | None,
    official_source_state: str | None = None,
    product_code: str | None = None,
    progressive: dict | None = None,
    product_revision: str | None = None,
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
        _empty_xcheck = build_official_cross_check(
            oset, plans, u,
            document_sha=document_sha,
            product_code=product_code,
            product_revision=product_revision,
            occurrence_results=[],
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
            "official_cross_check": _empty_xcheck,
            "release_consolidation": build_release_consolidation(
                oset,
                document_sha=document_sha,
                product_revision=product_revision,
                occurrence_results=[],
                cross_check=_empty_xcheck,
                comparison_blocked=comparison_blocked,
            ),
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
            occ, plan, table_rows, idents, document_sha, product_code,
            recovery=(u or {}).get("localized_recovery"),
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
                recheck = _targeted_recheck(
                    plan, box, progressive,
                    page=(row or {}).get("page") if row else None,
                )
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

    xcheck = build_official_cross_check(
        oset, plans, u,
        document_sha=document_sha,
        product_code=product_code,
        product_revision=product_revision,
        occurrence_results=results,
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
        "official_cross_check": xcheck,
        "release_consolidation": build_release_consolidation(
            oset,
            document_sha=document_sha,
            product_revision=product_revision,
            occurrence_results=results,
            cross_check=xcheck,
            comparison_blocked=comparison_blocked,
        ),
        "state": "DRAFT/CANDIDATE",
        "not_official": True,
        "human_review_required": True,
    }


def _rect_of(box: Any) -> list[float] | None:
    """Normaliza bounding box para ``[x1, y1, x2, y2]``.

    Células/tokens carregam quadriláteros de 8 pontos
    (``[x1,y1,x2,y2,x3,y3,x4,y4]``, top-left origin) — truncar em 4
    produzia faixa degenerada que perdia metade inferior da célula.
    """
    if not box or len(box) < 4:
        return None
    if len(box) >= 8:
        xs = [float(v) for v in box[0::2]]
        ys = [float(v) for v in box[1::2]]
        return [min(xs), min(ys), max(xs), max(ys)]
    return [float(box[0]), float(box[1]), float(box[2]), float(box[3])]


def _merge(dst: list[float], rect: list[float]) -> None:
    dst[0] = min(dst[0], rect[0])
    dst[1] = min(dst[1], rect[1])
    dst[2] = max(dst[2], rect[2])
    dst[3] = max(dst[3], rect[3])


def apply_localized_recovery(
    u: dict,
    *,
    product_code: str,
    bom_component_codes: list[str],
    opts: dict,
    tokens: list[dict] | None,
    pdf_sha256: str | None = None,
    source_revision: str | None = None,
) -> list[dict]:
    """DEC-VAL-034 — recuperação localizada + registro canônico da
    evidência no entendimento.

    Calcula os códigos oficiais ausentes da visão (células tipadas +
    tokens), aciona `recover_absent_table_cells` e registra o resultado
    nas três superfícies que consomem evidência:

    - ``tokens`` (comparador BOM×desenho);
    - ``u["code_contexts"]`` (contexto estrutural, dedup por
      code+region+page);
    - ``u["localized_recovery"]`` (contrato RQ-VAL-052 — consumido por
      ``_check_component_code`` na investigação guiada).

    Nunca fabrica evidência: só registra o que a percepção localizada
    observou. Retorna a lista de ocorrências recuperadas.
    """
    if not isinstance(u, dict):
        return []
    ct = u.get("component_table") or {}
    cell_codes = {
        str(c.get("text") or "").strip()
        for r in ct.get("rows") or []
        for c in r.get("cells") or []
        if is_component_code(c.get("text"))
    }
    visible = cell_codes | _token_code_set(tokens)
    missing = [
        str(c).strip()
        for c in (bom_component_codes or [])
        if str(c or "").strip() and str(c).strip() not in visible
    ]
    if not missing:
        return []
    recovered = recover_absent_table_cells(
        missing_codes=missing,
        component_table=ct,
        opts=opts or {},
        tokens=tokens,
    )
    for _rc in recovered:
        if tokens is not None:
            tokens.append(
                {
                    "normalized_text": _rc["code"],
                    "raw_text": _rc["observed_raw_value"],
                    "page": _rc["page"],
                    "confidence": _rc["confidence"],
                    "bounding_box_px": _rc["box"],
                    "provenance": "localized_ocr_recheck",
                }
            )
        _ctx_key = (_rc["code"], "component_table", _rc["page"])
        _ctxs = u.setdefault("code_contexts", [])
        if not any(
            (c.get("code"), c.get("region"), c.get("page")) == _ctx_key
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
                    "observed_raw_value": _rc["observed_raw_value"],
                }
            )
        u.setdefault("localized_recovery", []).append(
            {
                "observed_code": _rc["code"],
                "raw_text": _rc["observed_raw_value"],
                "product_code": product_code,
                "pdf_sha256": (
                    pdf_sha256 or u.get("document_hash_sha256")
                ),
                "page": _rc["page"],
                "region": "component_table",
                "region_box": _rc.get("region"),
                "region_ref_dpi": _rc.get("region_ref_dpi"),
                "bounding_box": _rc["box"],
                "coordinate_system": "pixels_pdfium_top_left",
                "method": _rc["method"],
                "confidence": _rc["confidence"],
                "source_revision": source_revision,
            }
        )
    return recovered


def recover_absent_table_cells(
    *,
    missing_codes: list[str],
    component_table: dict | None,
    opts: dict,
    tokens: list[dict] | None = None,
) -> list[dict]:
    """DEC-VAL-033 evolução — recuperação genérica de células de
    tabela densa perdidas pelo OCR de página inteira.

    Re-renderiza (crop nativo vetorial) cada faixa de tabela de
    componentes UMA vez e procura TODOS os códigos ausentes — 1 crop
    por faixa cobre N códigos. A região é a faixa de linhas da tabela
    tipada **expandida por tokens na mesma faixa vertical** — blocos
    de colunas paralelas que a segmentação não tipou (ex.: grupo
    ``Item|QTD|Componente`` à direita de ``Cabo|Código``) continuam
    dentro da inspeção. ``reference_dpi`` é resolvido por página
    (``opts["reference_dpi_by_page"]``) porque cada folha pode ser
    renderizada em resolução própria. Orçamento compartilhado com
    `_targeted_recheck` via ``opts["state"]["crops"]``; falha de
    render/OCR degrada honestamente, nunca derruba a análise.

    Retorna ocorrências ``{code, page, confidence, box, method}`` —
    presença com proveniência ``localized_ocr_recheck``; nunca inventa
    célula e nunca usa o código esperado como evidência (só conta
    quando o token OCR coincide com o código ou similaridade ≥0.85).
    """
    rows = (component_table or {}).get("rows") or []
    renderer = opts.get("renderer")
    ocr = opts.get("ocr")
    pdf_bytes = opts.get("pdf_bytes")
    if not rows or not renderer or not ocr or not pdf_bytes:
        return []
    regions: dict[int, list[float]] = {}
    for row in rows:
        page = int(row.get("page") or 1)
        for cell in row.get("cells") or []:
            rect = _rect_of(cell.get("bounding_box_px"))
            if rect is None:
                continue
            if page in regions:
                _merge(regions[page], rect)
            else:
                regions[page] = list(rect)
    if not regions:
        return []
    # Expansão por faixa: tokens cuja linha vertical coincide com a
    # faixa da tabela tipada pertencem ao mesmo material impresso —
    # blocos de colunas que a segmentação não tipou entram na região.
    y_band = {p: (r[1], r[3]) for p, r in regions.items()}
    for t in tokens or []:
        page = int(t.get("page") or 1)
        band = y_band.get(page)
        if band is None:
            continue
        rect = _rect_of(t.get("bounding_box_px"))
        if rect is None:
            continue
        if band[0] <= (rect[1] + rect[3]) / 2 <= band[1]:
            _merge(regions[page], rect)
    budget = opts.get("budget") or {}
    state = opts.setdefault("state", {"crops": 0})
    ref_by_page = opts.get("reference_dpi_by_page") or {}
    fallback_ref = int(opts.get("reference_dpi") or 150)
    max_px = int(budget.get("max_pixels", 4_000_000))
    max_crops = int(budget.get("max_crops", 8))
    max_dpi = min(int(budget.get("max_dpi", 300)), 300)
    remaining = {str(c) for c in missing_codes if c}
    found: list[dict] = []
    for page in sorted(regions):
        if not remaining or state["crops"] >= max_crops:
            break
        x1, y1, x2, y2 = regions[page]
        w_px, h_px = x2 - x1, y2 - y1
        if w_px <= 0 or h_px <= 0:
            continue
        ref_dpi = int(ref_by_page.get(page) or fallback_ref)
        # DPI adaptativo ao orçamento de pixels: render_px cresce com
        # dpi/ref_dpi e a margem aplicada no crop é contabilizada —
        # nunca abaixo do espaço de referência da página (crop com
        # menos resolução que a leitura original não agrega evidência).
        margin = 8
        w_eff, h_eff = w_px + 2 * margin, h_px + 2 * margin
        dpi_fit = int(ref_dpi * math.sqrt(max_px / (w_eff * h_eff)))
        dpi = min(max_dpi, max(dpi_fit, ref_dpi))
        try:
            region = renderer.render_region(
                pdf_bytes,
                page=page,
                region_px=regions[page],
                reference_dpi=ref_dpi,
                dpi=dpi,
                margin_px=margin,
            )
        except Exception:
            continue
        if region.width * region.height > max_px:
            continue
        state["crops"] += 1
        try:
            res = ocr.extract_text(region.image_bytes)
        except Exception:
            continue
        ox, oy = getattr(region, "offset_px", (0.0, 0.0)) or (0.0, 0.0)
        to_page = ref_dpi / float(region.dpi or dpi or ref_dpi)
        page_tokens = [
            (str(getattr(t, "text", "") or "").strip(),
             float(getattr(t, "confidence", 0.0) or 0.0),
             getattr(t, "bounding_box_px", None)
             or getattr(t, "box", None))
            for t in (getattr(res, "tokens", None) or [])
        ]
        for code in sorted(remaining):
            hit = next(
                (
                    (txt, conf, box)
                    for txt, conf, box in page_tokens
                    if txt == code or _similarity(code, txt) >= 0.85
                ),
                None,
            )
            if hit:
                box = _rect_of(hit[2])
                if box is not None:
                    box = [
                        (box[0] + ox) * to_page,
                        (box[1] + oy) * to_page,
                        (box[2] + ox) * to_page,
                        (box[3] + oy) * to_page,
                    ]
                found.append(
                    {
                        "code": code,
                        "page": page,
                        "confidence": hit[1],
                        "box": box or hit[2],
                        "region": list(regions[page]),
                        "region_ref_dpi": ref_dpi,
                        "observed_raw_value": hit[0],
                        "method": "localized_ocr_recheck",
                    }
                )
        remaining -= {f["code"] for f in found}
    return found
