"""Canonical TÉO capability ↔ transport binding registry.

Single inward source for the capability/parity contract. Adapters derive
their outward names from this registry — nothing in this module imports a
transport adapter (``tm_app.interface.*``).

Model:

- one :class:`CapabilityBinding` per semantic capability;
- ``actions_operation`` is the GPT Actions ``gpt_*`` operationId
  (``None`` = MCP-native capability — no fake parity);
- ``mcp_tools`` lists every MCP tool serving the capability (1→N allowed);
- ``mcp_primary`` is the explicit write-path/primary tool — REQUIRED for
  every binding, no naming heuristics;
- ``tool_class`` on each :class:`McpToolRef` is the MCP contract class
  (READ | PREPARE | ACT | ANALYSIS | DISCOVERY) — classes follow the tool,
  not the capability, because one capability (e.g. meeting_minute.manage)
  may span READ + ANALYSIS + PREPARE tools.

Fail closed: unknown capability ids, unknown transport names, and missing
or ambiguous mappings raise :class:`ProjectionContractError`. Known removed
legacy operations are explicit tombstones, never silent fallbacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PROJECTION_CONTRACT_ERROR = "projection_contract_error"


class ProjectionContractError(Exception):
    """Raised when a transport projection hits an unknown/ambiguous mapping.

    Fail closed by design: a drifted capability registry or an unknown
    ``gpt_*``/MCP name must surface as an invariant violation, never as a
    silently degraded payload.
    """

    def __init__(self, message: str, *, detail: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = PROJECTION_CONTRACT_ERROR
        self.detail = detail or {}


@dataclass(frozen=True)
class McpToolRef:
    """One MCP tool bound to a capability (name + contract class)."""

    name: str
    tool_class: str  # READ | PREPARE | ACT | ANALYSIS | DISCOVERY


@dataclass(frozen=True)
class CapabilityBinding:
    """One semantic capability with both transport projections."""

    id: str
    actions_operation: str | None  # gpt_* operationId; None = MCP-native
    mcp_tools: tuple[McpToolRef, ...]
    mcp_primary: str  # explicit primary/write-path tool — required, validated

    def __post_init__(self) -> None:
        names = {ref.name for ref in self.mcp_tools}
        if self.mcp_primary not in names:
            raise ProjectionContractError(
                f"Capability '{self.id}' primary '{self.mcp_primary}' "
                "is not bound to any MCP tool.",
                detail={"capability": self.id, "primary": self.mcp_primary},
            )
        if self.actions_operation is not None and not self.actions_operation.startswith(
            "gpt_"
        ):
            raise ProjectionContractError(
                f"Capability '{self.id}' actions_operation "
                f"'{self.actions_operation}' is not a gpt_* operationId.",
                detail={"capability": self.id},
            )


def _b(
    capability_id: str,
    actions_operation: str | None,
    *tools: tuple[str, str],
    primary: str,
) -> CapabilityBinding:
    return CapabilityBinding(
        id=capability_id,
        actions_operation=actions_operation,
        mcp_tools=tuple(McpToolRef(name=n, tool_class=c) for n, c in tools),
        mcp_primary=primary,
    )


# Canonical bindings — ONE semantic capability change updates BOTH
# transport projections. Order follows the historical parity contract.
CAPABILITY_BINDINGS: tuple[CapabilityBinding, ...] = (
    _b("context.self.read", "gpt_get_my_context", ("get_my_context", "READ"), primary="get_my_context"),
    _b("context.workspace.read", "gpt_get_workspace_context", ("get_workspace_context", "READ"), primary="get_workspace_context"),
    _b("catalog.read", "gpt_get_catalog", ("get_catalog", "DISCOVERY"), primary="get_catalog"),
    _b("methodology.read", "gpt_get_methodology_guide", ("get_methodology_guide", "READ"), primary="get_methodology_guide"),
    _b("product_guide.read", "gpt_get_product_guide", ("get_product_guide", "READ"), primary="get_product_guide"),
    _b("solutions.catalog.read", "gpt_get_solution_catalog", ("get_solution_catalog", "READ"), primary="get_solution_catalog"),
    _b("solutions.context.read", "gpt_get_solution_context", ("get_solution_context", "READ"), primary="get_solution_context"),
    _b("context.process.read", "gpt_get_process_context", ("get_process_context", "READ"), primary="get_process_context"),
    _b("analytics.read", "gpt_analyze", ("analyze", "READ"), primary="analyze"),
    _b("record.search", "gpt_search_records", ("search_records", "READ"), primary="search_records"),
    _b("record.read", "gpt_get_record", ("get_record", "READ"), primary="get_record"),
    _b("record.change.prepare", "gpt_prepare_record_change", ("prepare_record_change", "PREPARE"), primary="prepare_record_change"),
    _b("proposal.commit", "gpt_commit_proposal", ("commit_proposal", "ACT"), primary="commit_proposal"),
    _b("process_timeline.read", "gpt_get_process_timeline", ("get_process_timeline", "READ"), primary="get_process_timeline"),
    # Semantic family: special governed operations — single-action
    # capabilities share one PREPARE tool; policy stays per-capability.
    _b("revision.activate.prepare", "gpt_prepare_governed_operation", ("prepare_governed_operation", "PREPARE"), primary="prepare_governed_operation"),
    _b("dashboard.recalculate.prepare", "gpt_prepare_governed_operation", ("prepare_governed_operation", "PREPARE"), primary="prepare_governed_operation"),
    _b("improvement_package.prepare", "gpt_prepare_governed_operation", ("prepare_governed_operation", "PREPARE"), primary="prepare_governed_operation"),
    _b("shared_resource_cost.adjust.prepare", "gpt_prepare_governed_operation", ("prepare_governed_operation", "PREPARE"), primary="prepare_governed_operation"),
    # Semantic family: meeting minutes — reads (incl. transcript analysis)
    # on meeting_minute_read; workflow transitions + manage writes on
    # prepare_meeting_minute_change.
    _b("meeting_minute.read", "gpt_meeting_minute_read", ("meeting_minute_read", "READ"), primary="meeting_minute_read"),
    _b("meeting_minute.workflow.prepare", "gpt_prepare_meeting_minute_change", ("prepare_meeting_minute_change", "PREPARE"), primary="prepare_meeting_minute_change"),
    _b(
        "meeting_minute.manage",
        "gpt_prepare_meeting_minute_change",
        ("prepare_meeting_minute_change", "PREPARE"),
        primary="prepare_meeting_minute_change",
    ),
    # Semantic family: evidence (structured metadata only — binary
    # transfer stays platform_blocked).
    _b("evidence.list", "gpt_evidence_read", ("evidence_read", "READ"), primary="evidence_read"),
    _b("evidence.manage.prepare", "gpt_prepare_evidence_change", ("prepare_evidence_change", "PREPARE"), primary="prepare_evidence_change"),
    # Semantic family: collaboration — Transformômetro tasks
    # (TaskCommandUseCases) + interaction rooms/messages
    # (InteractionRoomUseCases; binary attachments stay UI-only).
    _b("task.read", "gpt_collaboration_read", ("collaboration_read", "READ"), primary="collaboration_read"),
    _b(
        "interaction_room.read",
        "gpt_collaboration_read",
        ("collaboration_read", "READ"),
        primary="collaboration_read",
    ),
    _b(
        "task.change.prepare",
        "gpt_prepare_collaboration_change",
        ("prepare_collaboration_change", "PREPARE"),
        primary="prepare_collaboration_change",
    ),
    _b(
        "interaction_room.change.prepare",
        "gpt_prepare_collaboration_change",
        ("prepare_collaboration_change", "PREPARE"),
        primary="prepare_collaboration_change",
    ),
    # MCP-native — no Actions surface; never fake a parity mapping.
    _b("diagnostic.read", None, ("diagnostic_read", "READ"), primary="diagnostic_read"),
    _b("diagnostic.list_by_revision", None, ("diagnostic_read", "READ"), primary="diagnostic_read"),
    _b("diagnostic.create.prepare", None, ("prepare_diagnostic_change", "PREPARE"), primary="prepare_diagnostic_change"),
    _b("diagnostic.manage.prepare", None, ("prepare_diagnostic_change", "PREPARE"), primary="prepare_diagnostic_change"),
)


# ---------------------------------------------------------------------------
# Derived projections (pure — adapters and surfaces consume these)
# ---------------------------------------------------------------------------


def actions_parity(
    bindings: tuple[CapabilityBinding, ...] = CAPABILITY_BINDINGS,
) -> dict[str, tuple[str, ...]]:
    """Actions operationId → bound MCP tool names (the canonical parity map).

    Multiple semantic capabilities may share one Actions operation (a
    semantic family); the parity map merges their tool refs, deduped in
    binding order.
    """
    parity: dict[str, list[str]] = {}
    for b in bindings:
        if b.actions_operation is None:
            continue
        tools = parity.setdefault(b.actions_operation, [])
        for ref in b.mcp_tools:
            if ref.name not in tools:
                tools.append(ref.name)
    return {op: tuple(tools) for op, tools in parity.items()}


def actions_to_mcp_primary(
    bindings: tuple[CapabilityBinding, ...] = CAPABILITY_BINDINGS,
) -> dict[str, str]:
    """Actions operationId → explicit primary MCP tool name."""
    return {
        b.actions_operation: b.mcp_primary
        for b in bindings
        if b.actions_operation is not None
    }


def mcp_primary_to_actions(
    bindings: tuple[CapabilityBinding, ...] = CAPABILITY_BINDINGS,
) -> dict[str, str]:
    """Primary/neutral MCP name → Actions operationId (inverse parity)."""
    return {
        b.mcp_primary: b.actions_operation
        for b in bindings
        if b.actions_operation is not None
    }


def mcp_tool_to_actions(
    bindings: tuple[CapabilityBinding, ...] = CAPABILITY_BINDINGS,
) -> dict[str, str]:
    """Every MCP tool name → owning Actions operationId (1→N preserved)."""
    return {
        ref.name: b.actions_operation
        for b in bindings
        for ref in b.mcp_tools
        if b.actions_operation is not None
    }


def mcp_native_tool_names(
    bindings: tuple[CapabilityBinding, ...] = CAPABILITY_BINDINGS,
) -> frozenset[str]:
    """MCP tools with no Actions binding (MCP-native capabilities)."""
    return frozenset(
        ref.name
        for b in bindings
        if b.actions_operation is None
        for ref in b.mcp_tools
    )


def mcp_tool_classes(
    bindings: tuple[CapabilityBinding, ...] = CAPABILITY_BINDINGS,
) -> dict[str, str]:
    """MCP tool name → contract class (READ|PREPARE|ACT|ANALYSIS|DISCOVERY)."""
    return {ref.name: ref.tool_class for b in bindings for ref in b.mcp_tools}


def all_mcp_tool_names(
    bindings: tuple[CapabilityBinding, ...] = CAPABILITY_BINDINGS,
) -> tuple[str, ...]:
    return tuple(ref.name for b in bindings for ref in b.mcp_tools)


def binding_for_capability(
    capability_id: str,
    bindings: tuple[CapabilityBinding, ...] = CAPABILITY_BINDINGS,
) -> CapabilityBinding:
    for binding in bindings:
        if binding.id == capability_id:
            return binding
    raise ProjectionContractError(
        f"Unknown canonical capability '{capability_id}'.",
        detail={"capability": capability_id},
    )


def actions_operation_for_neutral(
    neutral_name: str,
    bindings: tuple[CapabilityBinding, ...] = CAPABILITY_BINDINGS,
) -> str:
    """Fail-closed neutral→Actions name resolution for catalog projections."""
    op = mcp_primary_to_actions(bindings).get(neutral_name)
    if op is None:
        raise ProjectionContractError(
            f"Neutral capability name '{neutral_name}' has no Actions "
            "projection — unknown mapping or MCP-native capability.",
            detail={"neutral_name": neutral_name},
        )
    return op


# ---------------------------------------------------------------------------
# Confirmation-policy labels — transport projections of the same verdict
# ---------------------------------------------------------------------------

_CONFIRMATION_POLICY_LABELS = {
    "auto_act": {
        "gpt_actions": "commit_now_allowed_additive",
        "mcp": "auto_act",
    },
    "confirm_before_act": {
        "gpt_actions": "explicit_user_confirmation_before_commit",
        "mcp": "confirm_before_act",
    },
}


def confirmation_policy_label(kind: str, transport: str) -> str:
    labels = _CONFIRMATION_POLICY_LABELS.get(kind)
    if labels is None or transport not in labels:
        raise ProjectionContractError(
            f"Unknown confirmation-policy projection '{kind}'/'{transport}'.",
            detail={"kind": kind, "transport": transport},
        )
    return labels[transport]
