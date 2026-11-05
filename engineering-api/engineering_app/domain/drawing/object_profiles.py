"""Perfis reutilizáveis de objetos técnicos de desenho (doc 116-B).

Domain puro — dataclasses, sem framework/OCR/MCP. Separa dados oficiais
(BOM/Expected) de observações visuais (Observed/Candidate), hierarquia,
consumo×montagem×dimensão, relações auditáveis e verificações tipadas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

# Validador compartilhado de formato de código de componente (R12):
# fonte canônica única — produção e investigação usam a MESMA regra.
COMPONENT_CODE_RE = re.compile(r"^\d{6,11}(-\d+)?$")


def is_component_code(text: object) -> bool:
    """True se o texto tem formato canônico de código de componente."""
    return bool(COMPONENT_CODE_RE.match(str(text or "").strip()))


class ObjectType(str, Enum):
    BOM_OCCURRENCE = "bom_occurrence"
    DRAWING_TABLE_ITEM = "drawing_table_item"
    BALLOON = "balloon"
    DIMENSION = "dimension"
    DRAWING_GEOMETRY = "drawing_geometry"


class ObservationState(str, Enum):
    OBSERVED = "OBSERVED"
    EXPECTED = "EXPECTED"
    CANDIDATE = "CANDIDATE"
    UNKNOWN = "UNKNOWN"
    NOT_CHECKED = "NOT_CHECKED"


class VerificationState(str, Enum):
    MATCH = "MATCH"
    CONFLICT = "CONFLICT"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    PENDING_RULE_VALIDATION = "PENDING_RULE_VALIDATION"
    NOT_CHECKED = "NOT_CHECKED"
    UNKNOWN = "UNKNOWN"


class RelationType(str, Enum):
    REPRESENTED_BY = "REPRESENTED_BY"
    REFERENCED_BY = "REFERENCED_BY"
    POINTS_TO = "POINTS_TO"
    DIMENSIONS = "DIMENSIONS"
    REPRESENTS = "REPRESENTS"


@dataclass(frozen=True)
class DrawingObjectRef:
    """Referência tipada a evidência — preserva origem, nunca inventada."""
    source_kind: str            # "bom"|"ocr"|"slanet"|"region"|"manual"
    document_sha: str | None = None
    page: int | None = None
    bounding_box: list[float] | None = None
    raw_value: str | None = None
    # sistema de coordenadas do bbox (ex.: "pixels_pdfium_top_left")
    coordinate_system: str | None = None


@dataclass
class DrawingRelation:
    source_object_id: str
    target_object_id: str
    relation_type: RelationType
    evidence_refs: list[DrawingObjectRef] = field(default_factory=list)
    verification_state: VerificationState = VerificationState.NOT_CHECKED
    uncertainty_reason: str | None = None


@dataclass
class DrawingObject:
    """Elemento técnico — atributos tipados por perfil em `attributes`;
    dados oficiais identificados em `official` vs observações `observed`."""
    object_id: str
    object_type: ObjectType
    attributes: dict = field(default_factory=dict)
    document_identity: str | None = None
    location: DrawingObjectRef | None = None
    evidence_refs: list[DrawingObjectRef] = field(default_factory=list)
    relations: list[DrawingRelation] = field(default_factory=list)
    observation_state: ObservationState = ObservationState.CANDIDATE
    verification_state: VerificationState = VerificationState.NOT_CHECKED
    limitations: list[str] = field(default_factory=list)
    # separação explícita: dados oficiais vs observações visuais
    official: bool = False


def bom_occurrence(
    object_id: str, *, component_code: str, parent_code: str | None,
    bom_level: int, bom_path: str, consumption_quantity: str | None,
    consumption_unit: str | None, document_sha: str | None = None,
    component_description: str | None = None,
) -> DrawingObject:
    """Perfil A — ocorrência BOM (dado oficial, consumo ≠ montagem ≠ cota)."""
    return DrawingObject(
        object_id=object_id,
        object_type=ObjectType.BOM_OCCURRENCE,
        attributes={
            "component_code": component_code,
            "parent_code": parent_code,
            "bom_level": bom_level,
            "bom_path": bom_path,
            "consumption_quantity": consumption_quantity,
            "consumption_unit": consumption_unit,
            "component_description": component_description,
        },
        document_identity=document_sha,
        observation_state=ObservationState.EXPECTED,
        official=True,
        limitations=[
            "consumo da estrutura não equivale a quantidade de montagem"
        ],
    )


def table_item(
    object_id: str, *, item_label: str | None,
    assembly_quantity: str | None, component_code_candidate: str | None,
    description_candidate: str | None, table_region: str | None,
    document_sha: str | None = None, row_evidence: DrawingObjectRef | None = None,
    evidence_refs: list[DrawingObjectRef] | None = None,
    ambiguities: list[str] | None = None,
    extra_attributes: dict | None = None,
) -> DrawingObject:
    """Perfil B — item da tabela do desenho (observado, montagem ≠ consumo)."""
    attributes = {
        "item_label": item_label,
        "assembly_quantity": assembly_quantity,
        "component_code_candidate": component_code_candidate,
        "description_candidate": description_candidate,
        "table_region": table_region,
    }
    if ambiguities:
        attributes["ambiguities"] = list(ambiguities)
    if extra_attributes:
        attributes.update(extra_attributes)
    refs = [row_evidence] if row_evidence else []
    refs.extend(evidence_refs or [])
    return DrawingObject(
        object_id=object_id,
        object_type=ObjectType.DRAWING_TABLE_ITEM,
        attributes=attributes,
        document_identity=document_sha,
        evidence_refs=refs,
        observation_state=ObservationState.CANDIDATE,
        official=False,
        limitations=(
            [f"evidência ambígua: {a}" for a in (ambiguities or [])]
        ),
    )


def dimension(
    object_id: str, *, raw_value: str, unit: str | None,
    dimension_kind: str | None, document_sha: str | None = None,
    evidence_refs: list[DrawingObjectRef] | None = None,
) -> DrawingObject:
    """Perfil D — cota observada; nunca promove a geometria sem prova."""
    return DrawingObject(
        object_id=object_id,
        object_type=ObjectType.DIMENSION,
        attributes={
            "raw_value": raw_value,
            "numeric_value": raw_value,
            "unit": unit,
            "dimension_kind": dimension_kind,
            "geometry_linked": False,
        },
        document_identity=document_sha,
        evidence_refs=list(evidence_refs or []),
        observation_state=ObservationState.OBSERVED,
        official=False,
        limitations=[
            "associação a geometria exige relação explícita, não proximidade"
        ],
    )


def balloon(
    object_id: str, *, item_label: str | None,
    document_sha: str | None = None,
    evidence_refs: list[DrawingObjectRef] | None = None,
    extra_attributes: dict | None = None,
) -> DrawingObject:
    """Perfil C — balão somente quando realmente identificado na fonte."""
    attributes = {"item_label": item_label}
    if extra_attributes:
        attributes.update(extra_attributes)
    return DrawingObject(
        object_id=object_id,
        object_type=ObjectType.BALLOON,
        attributes=attributes,
        document_identity=document_sha,
        evidence_refs=list(evidence_refs or []),
        observation_state=ObservationState.CANDIDATE,
        official=False,
        limitations=[
            "vínculo balão↔item/geometria exige relação explícita"
        ],
    )


def drawing_geometry(
    object_id: str, *, region_type: str | None,
    document_sha: str | None = None,
    evidence_refs: list[DrawingObjectRef] | None = None,
) -> DrawingObject:
    """Perfil E — região de geometria candidata observada no desenho."""
    return DrawingObject(
        object_id=object_id,
        object_type=ObjectType.DRAWING_GEOMETRY,
        attributes={"region_type": region_type},
        document_identity=document_sha,
        evidence_refs=list(evidence_refs or []),
        observation_state=ObservationState.CANDIDATE,
        official=False,
        limitations=[
            "geometria candidata — associação a cotas/balões exige "
            "evidência espacial ou estrutural verificável"
        ],
    )


@dataclass
class VerificationSpec:
    """Especificação leve de verificação — política referenciada, nunca
    executada como regra definitiva se não aprovada."""
    verification_key: str
    target_object_type: ObjectType
    required_attributes: list[str]
    required_relation_types: list[RelationType]
    policy_reference: str | None = None
    policy_version: str | None = None
    result_state: VerificationState = VerificationState.PENDING_RULE_VALIDATION


class DrawingObjectSet:
    """Conjunto de objetos+relações com identidade única e integridade
    referencial — composição reutilizável, não source of truth."""

    def __init__(self, document_sha: str | None = None):
        self.document_sha = document_sha
        self._objects: dict[str, DrawingObject] = {}
        self._relations: list[DrawingRelation] = []

    def add_object(self, obj: DrawingObject) -> None:
        if obj.object_id in self._objects:
            raise ValueError(f"duplicate object_id: {obj.object_id}")
        self._objects[obj.object_id] = obj

    def add_relation(self, rel: DrawingRelation) -> None:
        for oid in (rel.source_object_id, rel.target_object_id):
            if oid not in self._objects:
                raise ValueError(f"dangling object ref: {oid}")
        self._relations.append(rel)

    def by_type(self, t: ObjectType) -> list[DrawingObject]:
        return [o for o in self._objects.values() if o.object_type is t]

    def by_component(self, code: str) -> list[DrawingObject]:
        return [
            o
            for o in self._objects.values()
            if o.attributes.get("component_code") == code
            or o.attributes.get("component_code_candidate") == code
        ]

    def relations(self) -> list[DrawingRelation]:
        return list(self._relations)

    def objects(self) -> list[DrawingObject]:
        return list(self._objects.values())

    def unverified(self) -> list[DrawingObject]:
        return [
            o
            for o in self._objects.values()
            if o.verification_state in {
                VerificationState.NOT_CHECKED,
                VerificationState.UNKNOWN,
            }
        ]
