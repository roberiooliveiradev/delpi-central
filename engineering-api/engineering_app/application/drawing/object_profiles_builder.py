"""Composição de perfis de objetos do desenho (R11) — converte evidências
existentes (`bom_occurrences` + `visual_observations`) em
`DrawingObjectSet` serializado. Aditivo, candidate/DRAFT, sem nova
pipeline nem source of truth."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any

from engineering_app.domain.drawing.object_profiles import (
    DrawingObjectSet,
    ObjectType,
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


def build_object_profiles(
    *, bom_occurrences: list[dict],
    visual_observations: list[dict],
    component_rows: list[dict] | None = None,
    document_sha: str | None = None,
) -> dict:
    """Monta o conjunto de perfis (oficial≠observado) + relações candidatas.

    `bom_occurrences` (oficial) e `component_rows` (observado) viram
    objetos tipados; relações REPRESENTED_BY são candidatas por
    correspondência de código — NUNCA verificadas por mera igualdade.
    """
    oset = DrawingObjectSet(document_sha=document_sha)
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
                document_sha=document_sha,
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
    # relações candidatas: table_item REPRESENTED_BY bom_occurrence por
    # component_code — candidata (não verificada por igualdade simples).
    items = oset.by_type(ObjectType.DRAWING_TABLE_ITEM)
    occs = oset.by_type(ObjectType.BOM_OCCURRENCE)
    from engineering_app.domain.drawing.object_profiles import (
        DrawingRelation,
        RelationType,
        VerificationState,
    )
    for it in items:
        code = it.attributes.get("component_code_candidate")
        if not code:
            continue
        for occ in occs:
            if occ.attributes.get("component_code") == code:
                oset.add_relation(
                    DrawingRelation(
                        source_object_id=occ.object_id,
                        target_object_id=it.object_id,
                        relation_type=RelationType.REPRESENTED_BY,
                        verification_state=VerificationState.NOT_CHECKED,
                        uncertainty_reason=(
                            "code_match é candidato — exige revisão técnica, "
                            "não vínculo automático"
                        ),
                    )
                )
    return {
        "contract_version": "drawing_object_profiles.v1",
        "document_sha": document_sha,
        "objects": [_object_to_dict(o) for o in oset.objects()],
        "relations": [_relation_to_dict(r) for r in oset.relations()],
        "state": "DRAFT/CANDIDATE",
        "not_official": True,
    }
