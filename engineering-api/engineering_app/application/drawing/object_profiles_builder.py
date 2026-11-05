"""Composição de perfis de objetos do desenho (R11) — converte evidências
existentes (`bom_occurrences` + `visual_observations` + `understanding`)
em `DrawingObjectSet` serializado. Aditivo, candidate/DRAFT, sem nova
pipeline nem source of truth."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any

from engineering_app.application.drawing.drawing_investigation import (
    execute_investigations,
    plan_investigations,
)
from engineering_app.application.drawing.understanding_object_mapper import (
    populate_from_understanding,
)
from engineering_app.domain.drawing.object_profiles import (
    DrawingObjectRef,
    DrawingObjectSet,
    DrawingRelation,
    ObjectType,
    RelationType,
    VerificationState,
    bom_occurrence,
    dimension,
    table_item,
)


def _ser(obj) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    return obj


def _object_to_dict(o) -> dict:
    d = asdict(o)
    d["object_type"] = _ser(o.object_type)
    d["observation_state"] = _ser(o.observation_state)
    d["verification_state"] = _ser(o.verification_state)
    return d


def _relation_to_dict(r) -> dict:
    d = asdict(r)
    d["relation_type"] = _ser(r.relation_type)
    d["verification_state"] = _ser(r.verification_state)
    return d


def _by_type(seq: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for v in seq:
        k = str(v[key])
        counts[k] = counts.get(k, 0) + 1
    return counts


def build_object_profiles(
    *, bom_occurrences: list[dict],
    visual_observations: list[dict],
    component_rows: list[dict] | None = None,
    understanding: dict | None = None,
    document_sha: str | None = None,
    official_source_ref: str | None = None,
    include_investigations: bool = False,
    official_source_state: str | None = None,
    product_code: str | None = None,
    progressive: dict | None = None,
    product_revision: str | None = None,
) -> dict:
    """Monta o conjunto de perfis (oficial≠observado) + relações candidatas.

    `document_sha` identifica o documento analisado (PDF do desenho);
    `official_source_ref` identifica a proveniência oficial da BOM —
    uma ocorrência oficial nunca vira evidência visual por receber o
    SHA do desenho.

    `understanding` (contrato drawing_understanding.v1) alimenta itens
    de tabela, cotas, geometria e balões via mapper — evidências
    ambíguas preservadas, nunca promovidas. Relações REPRESENTED_BY são
    candidatas por correspondência de código — NUNCA verificadas por
    mera igualdade.
    """
    oset = DrawingObjectSet(document_sha=document_sha)
    limitations: list[str] = [
        "consumo da estrutura, quantidade de montagem e cota são "
        "conceitos distintos — nunca comparados diretamente",
        "unidades brutas da estrutura sem contrato oficial de "
        "conversão permanecem PENDING_RULE_VALIDATION/NOT_COMPARABLE",
    ]
    ambiguous_total = 0
    for occ in bom_occurrences or []:
        oset.add_object(
            bom_occurrence(
                str(occ.get("occurrence_id") or f"occ:{occ.get('component_code')}"),
                component_code=str(occ.get("component_code") or ""),
                parent_code=occ.get("parent_code"),
                bom_level=int(occ.get("depth") or 0),
                bom_path=str(occ.get("path") or ""),
                consumption_quantity=occ.get("quantity_raw"),
                consumption_unit=occ.get("unit_raw"),
                component_description=occ.get("component_description"),
                document_sha=official_source_ref,
            )
        )
    for i, row in enumerate(component_rows or []):
        oset.add_object(
            table_item(
                f"row:{i}",
                item_label=row.get("item"),
                assembly_quantity=row.get("quantity"),
                component_code_candidate=row.get("component_code"),
                description_candidate=row.get("description"),
                table_region=row.get("region"),
                document_sha=document_sha,
            )
        )
    for i, dim in enumerate(visual_observations or []):
        if dim.get("kind") != "dimension":
            continue
        oset.add_object(
            dimension(
                f"dim:{i}",
                raw_value=str(dim.get("raw_value") or dim.get("value") or ""),
                unit=dim.get("unit"),
                dimension_kind=dim.get("dimension_kind"),
                document_sha=document_sha,
            )
        )
    u_summary: dict[str, Any] = {}
    if understanding:
        u_summary = populate_from_understanding(
            oset, understanding, document_sha=document_sha
        )
        limitations.extend(u_summary.get("limitations") or [])
        ambiguous_total += u_summary.get("ambiguous_observations") or 0
    u_doc = (understanding or {}).get("document_hash_sha256")

    # relações candidatas: table_item REPRESENTED_BY bom_occurrence por
    # component_code — candidata (não verificada por igualdade simples);
    # observações ambíguas nunca geram relação.
    items = oset.by_type(ObjectType.DRAWING_TABLE_ITEM)
    occs = oset.by_type(ObjectType.BOM_OCCURRENCE)
    for it in items:
        code = it.attributes.get("component_code_candidate")
        if not code or it.attributes.get("ambiguities"):
            continue
        for occ in occs:
            if occ.attributes.get("component_code") == code:
                # R13-02 — proveniência espacial completa: reutiliza as
                # evidências reais da observação (página/bbox/cell/coord).
                _ev = [
                    DrawingObjectRef(
                        source_kind="code_match",
                        document_sha=document_sha,
                        raw_value=code,
                    )
                ] + list(it.evidence_refs)
                oset.add_relation(
                    DrawingRelation(
                        source_object_id=occ.object_id,
                        target_object_id=it.object_id,
                        relation_type=RelationType.REPRESENTED_BY,
                        evidence_refs=_ev,
                        verification_state=VerificationState.NOT_CHECKED,
                        uncertainty_reason=(
                            "code_match é candidato — exige revisão técnica, "
                            "não vínculo automático"
                        ),
                    )
                )
    objects = [_object_to_dict(o) for o in oset.objects()]
    relations = [_relation_to_dict(r) for r in oset.relations()]
    out = {
        "contract_version": "drawing_object_profiles.v1",
        "document_sha": document_sha,
        "official_source_ref": official_source_ref,
        "document_identity": {
            "set_document_sha": document_sha,
            "understanding_document_sha": u_doc,
            "match": (
                None
                if not (document_sha and u_doc)
                else document_sha == u_doc
            ),
        },
        "understanding_integrated": bool(understanding),
        "objects": objects,
        "relations": relations,
        "objects_by_type": _by_type(objects, "object_type"),
        "relations_by_type": _by_type(relations, "relation_type"),
        "ambiguous_observations": ambiguous_total,
        "limitations": limitations,
        "state": "DRAFT/CANDIDATE",
        "not_official": True,
    }
    if include_investigations:
        plans = plan_investigations(oset)
        out["guided_investigations"] = execute_investigations(
            oset,
            plans,
            understanding,
            document_sha=document_sha,
            official_source_state=official_source_state,
            product_code=product_code,
            progressive=progressive,
            product_revision=product_revision,
        )
    return out
