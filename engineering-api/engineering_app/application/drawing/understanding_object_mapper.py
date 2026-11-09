"""Mapper ``drawing_understanding.v1`` → ``DrawingObjectSet`` (R11.1).

Converte os resultados existentes do Drawing Understanding (linhas de
tabela tipadas, cotas candidatas, regiões, balões quando identificados)
em objetos/relações do conjunto reutilizável — sem duplicar OCR/SLANet
e sem promover campos incorretos conhecidos.

Regras:
- ``quantity`` não numérica, código fora de formato ou associação não
  resolvida → evidência bruta preservada + observação marcada ambígua;
  observação ambígua NUNCA gera relação.
- Balões/geometria só existem quando a fonte os identifica; ausência →
  zero objetos + limitação explícita (nenhuma relação artificial).
- Toda evidência carrega página, bounding box e sistema de coordenadas
  do contrato de origem (``pixels_pdfium_top_left``).
"""

from __future__ import annotations

import re
from typing import Any

from engineering_app.domain.drawing.object_profiles import (
    COMPONENT_CODE_RE as _CODE_RE,
    DrawingObjectRef,
    DrawingObjectSet,
    DrawingRelation,
    ObjectType,
    RelationType,
    VerificationState,
    balloon,
    dimension,
    drawing_geometry,
    table_item,
)

_COORD_SYSTEM = "pixels_pdfium_top_left"
_QTY_RE = re.compile(r"^\d+([.,]\d+)?$")
_DIM_UNIT_RE = re.compile(r"(mm|pol|in)\b", re.IGNORECASE)
_GEOMETRY_REGION_TYPES = {"drawing_area", "geometry", "figure", "view"}


def _quad_center(box: list[float] | None) -> tuple[float, float] | None:
    """Centro de bbox quad (8 valores) ou xyxy (4 valores)."""
    if not box or len(box) < 4:
        return None
    if len(box) >= 8:
        xs = [float(v) for v in box[0::2]]
        ys = [float(v) for v in box[1::2]]
        return (sum(xs) / len(xs), sum(ys) / len(ys))
    return ((float(box[0]) + float(box[2])) / 2,
            (float(box[1]) + float(box[3])) / 2)


def _inside_box(
    center: tuple[float, float] | None, box: list[float] | None
) -> bool:
    return bool(
        center and box and len(box) >= 4
        and box[0] <= center[0] <= box[2]
        and box[1] <= center[1] <= box[3]
    )


def _unit_of(text: str) -> str | None:
    """Unidade só quando explicitamente escrita (limitação do contrato)."""
    m = _DIM_UNIT_RE.search(text or "")
    return m.group(1).lower() if m else None


def _ref(
    *,
    source_kind: str = "drawing_understanding",
    document_sha: str | None,
    page: int | None = None,
    bounding_box: list[float] | None = None,
    raw_value: str | None = None,
) -> DrawingObjectRef:
    return DrawingObjectRef(
        source_kind=source_kind,
        document_sha=document_sha,
        page=page,
        bounding_box=list(bounding_box) if bounding_box else None,
        raw_value=raw_value,
        coordinate_system=_COORD_SYSTEM if bounding_box else None,
    )


def populate_from_understanding(
    oset: DrawingObjectSet,
    understanding: dict[str, Any],
    *,
    document_sha: str | None,
) -> dict[str, Any]:
    """Popula ``oset`` com os perfis observados do ``understanding``.

    Retorna sumário com contagens, ambiguidades e limitações para o
    serializer do builder — nenhum estado promovido silenciosamente.
    """
    u = understanding or {}
    u_doc = u.get("document_hash_sha256") or document_sha
    u_page = u.get("page")
    limits: list[str] = []
    ambiguities_total = 0
    added = 0
    relations_added = 0

    # ---------- itens candidatos de tabela (perfil B) ----------
    comp = u.get("component_table") or {}
    rows = comp.get("rows") or []
    if comp.get("unreliable_boundary"):
        limits.append(
            "tabela com fronteira não confiável — itens permanecem "
            "candidatos sem promoção"
        )
    for i, row in enumerate(rows):
        fields = row.get("fields") or {}
        assoc = row.get("association_status")

        def _fval(name: str) -> str | None:
            f = fields.get(name) or {}
            v = f.get("normalized_value") or f.get("raw_text")
            v = str(v).strip() if v is not None else ""
            return v or row.get(name) or None

        ambiguities: list[str] = []
        qty_raw = _fval("quantity")
        code_raw = _fval("component_code")
        qty = code = None
        if qty_raw and not _QTY_RE.match(qty_raw):
            ambiguities.append("quantity_not_numeric")
        else:
            qty = qty_raw
        if code_raw and not _CODE_RE.match(code_raw):
            ambiguities.append("component_code_not_code_shaped")
        else:
            code = code_raw
        if assoc != "FIELD_IDENTIFIED" and not fields:
            ambiguities.append("association_unresolved")
        n_amb = sum(
            1 for c in (row.get("cells") or []) if c.get("ambiguous")
        )
        if n_amb:
            ambiguities.append(f"ambiguous_cells:{n_amb}")
        if row.get("conflicting_fields") or row.get("association_conflict"):
            ambiguities.append("geometric_band_conflict")

        refs = [
            _ref(
                document_sha=u_doc,
                page=row.get("page", u_page),
                bounding_box=f.get("bounding_box_px"),
                raw_value=f.get("raw_text"),
            )
            for name in ("item", "quantity", "component_code",
                         "description")
            for f in [fields.get(name) or {}]
            if f.get("bounding_box_px")
        ]
        row_ref = refs[0] if refs else _ref(
            document_sha=u_doc,
            page=row.get("page", u_page),
            raw_value=str(row.get("row", i)),
        )
        extra = {
            k: v
            for k, v in {
                "assembly_quantity_raw": qty_raw if qty is None else None,
                "component_code_candidate_raw": (
                    code_raw if code is None else None
                ),
                "association_status": assoc,
                "row": row.get("row"),
                "y_px": row.get("y_px"),
            }.items()
            if v is not None
        }
        oset.add_object(
            table_item(
                f"urow:{i}",
                item_label=_fval("item"),
                assembly_quantity=qty,
                component_code_candidate=code,
                description_candidate=_fval("description"),
                table_region="component_table",
                document_sha=u_doc,
                row_evidence=row_ref,
                evidence_refs=refs,
                ambiguities=ambiguities or None,
                extra_attributes=extra or None,
            )
        )
        added += 1
        ambiguities_total += bool(ambiguities)

    # ---------- cotas observadas (perfil D) ----------
    geo_objs: list = []
    bal_objs: list = []
    for i, d in enumerate(u.get("dimension_candidates") or []):
        dobj = dimension(
            f"udim:{i}",
            raw_value=str(d.get("text") or ""),
            unit=_unit_of(str(d.get("text") or "")),
            dimension_kind=d.get("state"),
            document_sha=u_doc,
            evidence_refs=[
                _ref(
                    document_sha=u_doc,
                    page=d.get("page", u_page),
                    bounding_box=d.get("bounding_box_px"),
                    raw_value=d.get("text"),
                )
            ],
        )
        dobj.attributes["region"] = d.get("region")
        dobj.attributes["rule"] = d.get("rule")
        oset.add_object(dobj)
        added += 1

    # ---------- regiões de geometria candidatas (perfil E) ----------
    geo_sources = [
        r
        for r in (u.get("regions") or [])
        if r.get("type") in _GEOMETRY_REGION_TYPES
    ]
    geo_sources += list(u.get("geometry_regions") or [])
    geo_id_map: dict[str, Any] = {}
    for i, g in enumerate(geo_sources):
        refs = [
            _ref(
                source_kind="region",
                document_sha=u_doc,
                page=g.get("page", u_page),
                bounding_box=g.get("box_px") or g.get("bounding_box_px"),
                raw_value=g.get("type"),
            )
        ]
        gobj = drawing_geometry(
            f"ugeo:{i}",
            region_type=g.get("type"),
            document_sha=u_doc,
            evidence_refs=refs,
        )
        oset.add_object(gobj)
        geo_objs.append(
            (gobj, g.get("box_px") or g.get("bounding_box_px"))
        )
        gid = g.get("id") or g.get("region_id")
        if gid:
            geo_id_map[gid] = gobj
        added += 1
    if not geo_objs:
        limits.append(
            "nenhuma região de geometria identificada — relações "
            "cota→geometria não compostas"
        )

    # ---------- balões (perfil C) — somente quando identificados ----
    # R13 — balões declarados + detectados por primitiva circular
    # (primitive_containment): evidência própria, nunca fabricados.
    from engineering_app.application.drawing.drawing_investigation import (
        identify_balloon_candidates,
    )

    bal_sources = list(u.get("balloons") or [])
    if not bal_sources:
        bal_sources = identify_balloon_candidates(u)
    for i, b in enumerate(bal_sources):
        bobj = balloon(
            f"ubal:{i}",
            item_label=b.get("item_label"),
            document_sha=u_doc,
            evidence_refs=[
                _ref(
                    document_sha=u_doc,
                    page=b.get("page", u_page),
                    bounding_box=b.get("bounding_box_px"),
                    raw_value=b.get("item_label"),
                )
            ],
            extra_attributes={
                "identification_method": b.get(
                    "identification_method", "declared"
                ),
            },
        )
        oset.add_object(bobj)
        bal_objs.append((bobj, b.get("bounding_box_px") or []))
        added += 1
    if not bal_objs:
        limits.append(
            "balões não identificados pela pipeline — relações "
            "item→balão→geometria não compostas"
        )

    # ---------- relações candidatas (somente com evidência) ----------
    # DRAWING_TABLE_ITEM → BALLOON: rótulo idêntico identificado.
    items = oset.by_type(ObjectType.DRAWING_TABLE_ITEM)
    for it in items:
        label = it.attributes.get("item_label")
        if not label or it.attributes.get("ambiguities"):
            continue
        for bo, _bb in bal_objs:
            if bo.attributes.get("item_label") == label:
                oset.add_relation(
                    DrawingRelation(
                        source_object_id=it.object_id,
                        target_object_id=bo.object_id,
                        relation_type=RelationType.REFERENCED_BY,
                        evidence_refs=[_ref(
                            source_kind="label_match",
                            document_sha=u_doc,
                            raw_value=label,
                        )],
                        verification_state=VerificationState.NOT_CHECKED,
                        uncertainty_reason=(
                            "rótulo de balão igual ao item é candidato — "
                            "não verificado"
                        ),
                    )
                )
                relations_added += 1
    # BALLOON → DRAWING_GEOMETRY: alvo declarado na fonte; fallback por
    # contenção do contorno na região geométrica (candidato, não verificado).
    for bo, bbox in bal_objs:
        target_id = None
        for b in bal_sources:
            if b.get("item_label") == bo.attributes.get("item_label"):
                target_id = b.get("points_to") or b.get("target_region")
        if not target_id and bbox:
            bc = _quad_center(bbox)
            for gobj, gbox in geo_objs:
                if gbox and _inside_box(bc, gbox):
                    target_id = gobj.object_id
                    break
            if target_id:
                oset.add_relation(
                    DrawingRelation(
                        source_object_id=bo.object_id,
                        target_object_id=target_id,
                        relation_type=RelationType.POINTS_TO,
                        evidence_refs=[_ref(
                            source_kind="spatial_containment",
                            document_sha=u_doc,
                            bounding_box=bbox,
                            raw_value=bo.attributes.get("item_label"),
                        )],
                        verification_state=VerificationState.NOT_CHECKED,
                        uncertainty_reason=(
                            "contenção espacial é candidata — "
                            "não verificada"
                        ),
                    )
                )
                relations_added += 1
                continue
        if target_id and target_id in geo_id_map:
            oset.add_relation(
                DrawingRelation(
                    source_object_id=bo.object_id,
                    target_object_id=geo_id_map[target_id].object_id,
                    relation_type=RelationType.POINTS_TO,
                    evidence_refs=[_ref(
                        source_kind="declared_link",
                        document_sha=u_doc,
                        raw_value=str(target_id),
                    )],
                    verification_state=VerificationState.NOT_CHECKED,
                    uncertainty_reason="vínculo declarado — não verificado",
                )
            )
            relations_added += 1
    # DIMENSION → DRAWING_GEOMETRY: centro da cota contido na região.
    for i, d in enumerate(u.get("dimension_candidates") or []):
        center = _quad_center(d.get("bounding_box_px"))
        for gobj, gbox in geo_objs:
            if _inside_box(center, gbox):
                oset.add_relation(
                    DrawingRelation(
                        source_object_id=f"udim:{i}",
                        target_object_id=gobj.object_id,
                        relation_type=RelationType.DIMENSIONS,
                        evidence_refs=[_ref(
                            source_kind="spatial_containment",
                            document_sha=u_doc,
                            page=d.get("page", u_page),
                            bounding_box=d.get("bounding_box_px"),
                            raw_value=d.get("text"),
                        )],
                        verification_state=VerificationState.NOT_CHECKED,
                        uncertainty_reason=(
                            "contenção espacial é evidência candidata — "
                            "não verifica associação cota↔geometria"
                        ),
                    )
                )
                relations_added += 1
                break

    # ---------- limitações estruturais ----------
    ownership_conflicts = u.get("ownership_conflicts") or []
    if ownership_conflicts:
        limits.append(
            f"{len(ownership_conflicts)} conflitos de ownership de "
            "tokens — evidência contestada entre regiões"
        )
    bom_cmp = u.get("bom_comparison") or {}
    if bom_cmp.get("state") == "NOT_COMPARABLE":
        limits.append(
            "comparação BOM×tabela não comparável — ausência na tabela "
            "não afirmável"
        )

    return {
        "objects_added": added,
        "relations_added": relations_added,
        "ambiguous_observations": ambiguities_total,
        "limitations": limits,
    }
