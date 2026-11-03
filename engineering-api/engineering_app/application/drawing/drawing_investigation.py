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
    occ, plan, table_rows, idents, document_sha
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


def execute_investigations(
    oset,
    plans: list[dict],
    understanding: dict | None,
    *,
    document_sha: str | None,
) -> dict[str, Any]:
    """Executor I-01..I-05 sobre o mesmo DrawingObjectSet."""
    u = understanding or {}
    u_doc = u.get("document_hash_sha256")
    identity_conflict = bool(
        document_sha and u_doc and document_sha != u_doc
    )
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
        c1 = _check_component_code(occ, plan, table_rows, idents, document_sha)
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

    # I-05 — reconciliação independente: desenho → estrutura oficial.
    unmatched = []
    for c in table_rows:
        code = c["code"]
        if code and code not in bom_codes and is_component_code(code):
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
            if t and t not in bom_codes:
                unmatched.append(
                    {
                        "candidate_type": "identifier",
                        "observed_raw_value": t,
                        "region": region,
                        "state": "UNMATCHED_DRAWING_CANDIDATE",
                        "reason": "identificador sem correspondente "
                        "oficial",
                    }
                )

    return {
        "schema_version": INVESTIGATION_SCHEMA,
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
        "summary": {
            **totals,
            "unmatched_drawing_candidates": len(unmatched),
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
