"""Entity catalog for the Custom GPT Actions facade."""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet


class GptEntity(str, Enum):
    BRANCH = "branch"
    DEPARTMENT = "department"
    PROCESS = "process"
    INSTANCE = "instance"
    REVISION = "revision"
    MEASUREMENT = "measurement"
    INVESTMENT = "investment"
    SHARED_RESOURCE = "shared_resource"
    RESOURCE_COST = "resource_cost"
    RESOURCE_LINK = "resource_link"
    MEETING_MINUTE = "meeting_minute"
    DECOMPOSITION_TREE = "decomposition_tree"
    INSTANCE_DECOMPOSITION_SCOPE = "instance_decomposition_scope"
    REVISION_DECOMPOSITION_OVERLAY = "revision_decomposition_overlay"
    PROCESS_DIAGRAM = "process_diagram"
    INSTANCE_DIAGRAM_SCOPE = "instance_diagram_scope"
    REVISION_DIAGRAM_OVERLAY = "revision_diagram_overlay"
    IMPACT_EFFORT_MATRIX = "impact_effort_matrix"


class GptAnalysisView(str, Enum):
    META = "meta"
    SUMMARY = "summary"
    PROCESSES = "processes"
    INSTANCES = "instances"
    ROWS = "rows"


class GptMeetingMinuteWorkflow(str, Enum):
    SEND = "send"
    FINALIZE = "finalize"
    CANCEL = "cancel"


# Capabilities per entity: search, get, create, update, delete, duplicate
ENTITY_CAPABILITIES: dict[GptEntity, FrozenSet[str]] = {
    GptEntity.BRANCH: frozenset({"search", "get", "create", "update", "delete"}),
    GptEntity.DEPARTMENT: frozenset({"search", "get", "create", "update", "delete"}),
    GptEntity.PROCESS: frozenset(
        {"search", "get", "create", "update", "delete", "duplicate"}
    ),
    GptEntity.INSTANCE: frozenset(
        {"search", "get", "create", "update", "delete", "duplicate"}
    ),
    GptEntity.REVISION: frozenset(
        {"search", "get", "create", "update", "delete", "duplicate"}
    ),
    GptEntity.MEASUREMENT: frozenset({"search", "get", "create", "update"}),
    GptEntity.INVESTMENT: frozenset({"search", "get", "create", "update", "delete"}),
    GptEntity.SHARED_RESOURCE: frozenset(
        {"search", "get", "create", "update", "delete"}
    ),
    GptEntity.RESOURCE_COST: frozenset({"search", "get", "create", "update", "delete"}),
    GptEntity.RESOURCE_LINK: frozenset({"search", "get", "create", "update", "delete"}),
    GptEntity.MEETING_MINUTE: frozenset(
        {"search", "get", "create", "update", "delete"}
    ),
    GptEntity.DECOMPOSITION_TREE: frozenset({"get", "create", "update"}),
    GptEntity.INSTANCE_DECOMPOSITION_SCOPE: frozenset({"get", "create", "update"}),
    GptEntity.REVISION_DECOMPOSITION_OVERLAY: frozenset({"get", "create", "update"}),
    GptEntity.PROCESS_DIAGRAM: frozenset({"get", "create", "update"}),
    GptEntity.INSTANCE_DIAGRAM_SCOPE: frozenset({"get", "create", "update"}),
    GptEntity.REVISION_DIAGRAM_OVERLAY: frozenset({"get", "create", "update"}),
    GptEntity.IMPACT_EFFORT_MATRIX: frozenset({"get", "update"}),
}

ENTITY_DESCRIPTIONS: dict[GptEntity, str] = {
    GptEntity.BRANCH: "Operational unit (filial). Catalog admin.",
    GptEntity.DEPARTMENT: "Department (setor) linked to one or more units.",
    GptEntity.PROCESS: "Master process (processo-mestre).",
    GptEntity.INSTANCE: "Operational improvement (melhoria = process × unit × departments).",
    GptEntity.REVISION: "Calculable scenario (baseline/melhoria/automacao/correcao).",
    GptEntity.MEASUREMENT: "Monthly measurement for a revision (upsert by revisao_id).",
    GptEntity.INVESTMENT: "Investment line on a revision.",
    GptEntity.SHARED_RESOURCE: "Shared resource (license/tool) catalog.",
    GptEntity.RESOURCE_COST: "Cost validity period for a shared resource.",
    GptEntity.RESOURCE_LINK: "Link between a revision and a shared resource.",
    GptEntity.MEETING_MINUTE: "Transforma+ meeting minute (ata).",
    GptEntity.DECOMPOSITION_TREE: "Process WBS/decomposition tree (id = processo_id).",
    GptEntity.INSTANCE_DECOMPOSITION_SCOPE: "Instance WBS scope (id = instancia_id).",
    GptEntity.REVISION_DECOMPOSITION_OVERLAY: "Revision WBS overlay (id = revisao_id).",
    GptEntity.PROCESS_DIAGRAM: "Process macro flowchart (id = processo_id).",
    GptEntity.INSTANCE_DIAGRAM_SCOPE: "Instance diagram scope (id = instancia_id).",
    GptEntity.REVISION_DIAGRAM_OVERLAY: "Revision diagram overlay (id = revisao_id).",
    GptEntity.IMPACT_EFFORT_MATRIX: "Impact×effort matrix for a revision (id = revisao_id).",
}


def parse_entity(value: str) -> GptEntity:
    try:
        return GptEntity(str(value or "").strip())
    except ValueError as exc:
        allowed = ", ".join(e.value for e in GptEntity)
        raise ValueError(f"Unknown entity '{value}'. Allowed: {allowed}") from exc


def entity_supports(entity: GptEntity, capability: str) -> bool:
    return capability in ENTITY_CAPABILITIES.get(entity, frozenset())
