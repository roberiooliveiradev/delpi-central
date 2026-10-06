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
    PROCESS_DOCUMENT = "process_document"
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
    # Live dashboard projections (DashboardLiveService / canonical owners).
    DASHBOARD_SUMMARY_LIVE = "dashboard_summary_live"
    DASHBOARD_PROCESS_RANKING = "dashboard_process_ranking"
    DASHBOARD_ALERTS = "dashboard_alerts"
    DASHBOARD_EVOLUTION = "dashboard_evolution"
    DASHBOARD_BY_FAMILY = "dashboard_by_family"
    DASHBOARD_DUE_DATES = "dashboard_due_dates"
    DASHBOARD_STRATEGIC_INDICATORS = "dashboard_strategic_indicators"
    PROCESSES_CALCULATED = "processes_calculated"
    # Process/revision-scoped compute views (no persistence).
    PROCESS_REVISION_COMPARISON = "process_revision_comparison"
    IMPACT_EFFORT_MATRIX = "impact_effort_matrix"
    DECOMPOSITION_LINK_VALIDATION = "decomposition_link_validation"
    DECOMPOSITION_DRAFT_SUGGESTION = "decomposition_draft_suggestion"
    DIAGRAM_VALIDATION = "diagram_validation"
    DIAGRAM_BPMN_XML = "diagram_bpmn_xml"
    REVISION_ALLOCATION_DIAGNOSTIC = "revision_allocation_diagnostic"
    REVISION_DIAGRAM_MERGED = "revision_diagram_merged"
    REVISION_DECOMPOSITION_MERGED = "revision_decomposition_merged"


class GptMeetingMinuteWorkflow(str, Enum):
    SEND = "send"
    FINALIZE = "finalize"
    CANCEL = "cancel"
    # Authenticated refusal of a signature invite — distinct from public
    # token refusal; legally lighter than sign but still a recorded decision.
    REFUSE = "refuse"


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
    GptEntity.PROCESS_DOCUMENT: frozenset(
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
    GptEntity.PROCESS_DOCUMENT: (
        "Process textual documentation (Markdown). Not meeting minute, "
        "not structured process state, not flowchart."
    ),
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
