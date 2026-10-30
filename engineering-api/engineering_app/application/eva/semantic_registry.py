"""EVA semantic action registry — typed allowlist (EVA.MCP.SEMANTIC.R1).

Pure-data model, no transport/framework imports: the six public MCP
tools dispatch on ``(entity, action)`` — never on URLs, HTTP methods,
SQL or model-supplied function names. New Engineering capabilities
are added here as registry entries, never as new MCP tools.

Classification legend (``risk``):
- ``read``        — official facts, no side effects;
- ``analysis``    — derived, labeled computation over official facts;
- ``moderate``    — non-destructive mutation (create/update);
- ``destructive`` — delete / replace-all import — sealed proposal only.

``status``: ``proven`` = executed and evidenced; ``planned`` /
``not_implemented`` are catalogued honestly, never executable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SEMANTIC_CATALOG_VERSION = "1.0"

SEMANTIC_TOOL_NAMES: tuple[str, ...] = (
    "get_context",
    "read",
    "analyze",
    "knowledge",
    "execute",
    "delete",
)


@dataclass(frozen=True)
class SemanticAction:
    entity: str
    action: str
    tool: str
    description: str
    risk: str
    status: str = "proven"
    destructive: bool = False
    ref_arg: str | None = None
    ref_description: str | None = None
    requires: tuple[str, ...] = ()
    fields: tuple[str, ...] = ()
    phases: tuple[str, ...] = ()
    paginated: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def capability(self) -> str:
        return f"{self.entity}.{self.action}"

    def public_dict(self) -> dict:
        out: dict = {
            "entity": self.entity,
            "action": self.action,
            "tool": self.tool,
            "description": self.description,
            "risk": self.risk,
            "status": self.status,
        }
        if self.destructive:
            out["destructive"] = True
        if self.ref_arg:
            out["ref_arg"] = self.ref_arg
            if self.ref_description:
                out["ref_description"] = self.ref_description
        if self.requires:
            out["requires"] = list(self.requires)
        if self.fields:
            out["fields"] = list(self.fields)
        if self.phases:
            out["phases"] = list(self.phases)
        if self.paginated:
            out["paginated"] = True
        if self.notes:
            out["notes"] = list(self.notes)
        return out


def _a(
    entity: str,
    action: str,
    tool: str,
    description: str,
    risk: str,
    **kw,
) -> SemanticAction:
    return SemanticAction(
        entity=entity,
        action=action,
        tool=tool,
        description=description,
        risk=risk,
        **kw,
    )


_NC_LIST_FIELDS = (
    "status", "sale_number", "lmp_number", "customer_name", "product_code",
    "problem_tag", "date_start", "date_end", "sort_by", "sort_dir",
)
_LMP_PERIOD_FIELDS = ("start_date", "end_date", "branch")
# Writable NC fields — mirrors the official E-NC-07/08 contract; the
# authoritative check stays in tool_bridge.NC_WRITABLE_FIELDS (unknown
# keys are rejected there, never silently dropped).
_NC_WRITE_FIELDS = (
    "status", "sale_number", "lmp_number", "customer_name",
    "occurrence_date", "launch_date", "last_revision_date",
    "executed_by", "released_by", "defect_description",
    "corrective_actions", "technical_opinion", "problem_tags",
    "products", "registered_at",
)

SEMANTIC_ACTIONS: tuple[SemanticAction, ...] = (
    # --- get_context ------------------------------------------------------
    _a(
        "catalog", "capabilities", "get_context",
        "Live capability discovery: entities, actions, schemas, risk, "
        "phases and honest availability — call before any other tool.",
        "read",
    ),
    # --- read: engineering ------------------------------------------------
    _a(
        "engineering", "home", "read",
        "Authorized Engineering workspace: sections, attention items, "
        "tasks, requests and LMPs with per-source availability.",
        "read",
    ),
    _a(
        "engineering", "overview", "read",
        "Official Engineering indicators (3 LMP + 3 TRANSFORMA+) with "
        "values, units, period, scope and provenance — never recalculated.",
        "read",
        fields=("start_date", "end_date", "competence", "branch"),
    ),
    # --- read: lmp ----------------------------------------------------------
    _a(
        "lmp", "list", "read",
        "Engineering LMP/sales-order dashboard list with period and "
        "status filters.",
        "read",
        fields=_LMP_PERIOD_FIELDS + ("listing_type", "status"),
        paginated=True,
    ),
    _a(
        "lmp", "summary", "read",
        "Aggregated official LMP summary for the period.",
        "read", fields=_LMP_PERIOD_FIELDS,
    ),
    _a(
        "lmp", "detail", "read",
        "Single LMP/sales-order detail by sale number.",
        "read", ref_arg="sale_number",
        ref_description="Sales order number (e.g. 003306).",
        fields=_LMP_PERIOD_FIELDS,
    ),
    _a(
        "lmp", "history_events", "read",
        "Chronological event history of an LMP.",
        "read", ref_arg="sale_number",
        fields=_LMP_PERIOD_FIELDS + ("revision",),
    ),
    _a(
        "lmp", "history_flow", "read",
        "Stage/flow timeline of an LMP.",
        "read", ref_arg="sale_number",
        fields=_LMP_PERIOD_FIELDS + ("revision",),
    ),
    _a(
        "lmp", "goal_context", "read",
        "Official goal context for eligible LMP indicators.",
        "read", fields=_LMP_PERIOD_FIELDS,
    ),
    _a(
        "lmp", "department_idd", "read",
        "Departmental IDD indicator by competence.",
        "read", fields=("competence",) + _LMP_PERIOD_FIELDS,
    ),
    _a(
        "lmp", "nc_streak", "read",
        "Days-without-nonconformity streak indicator.",
        "read",
    ),
    # --- read: product ------------------------------------------------------
    _a(
        "product", "structure", "read",
        "Official product structure/BOM tree from the owning source.",
        "read", ref_arg="product_code",
        ref_description="Product code in the official catalog.",
        fields=("max_depth", "page_size"),
    ),
    # --- read: nonconformity ------------------------------------------------
    _a(
        "nonconformity", "search", "read",
        "Search nonconformities with filters, sorting and pagination.",
        "read", fields=_NC_LIST_FIELDS,
        paginated=True,
    ),
    _a(
        "nonconformity", "detail", "read",
        "Full nonconformity record by id.",
        "read", ref_arg="record_id", ref_description="NC UUID.",
    ),
    _a(
        "nonconformity", "history", "read",
        "Append-only audit history of a nonconformity.",
        "read", ref_arg="record_id",
    ),
    _a(
        "nonconformity", "indicators", "read",
        "Official nonconformity indicators (totals, open, streak).",
        "read",
    ),
    _a(
        "nonconformity", "tags", "read",
        "Nonconformity problem tags in use.",
        "read",
    ),
    _a(
        "nonconformity", "context", "read",
        "Contextual official data around a nonconformity (LMP, product).",
        "read", ref_arg="record_id",
    ),
    _a(
        "nonconformity", "export", "read",
        "Full nonconformity export (all records, official format).",
        "read",
    ),
    # --- analyze ------------------------------------------------------------
    _a(
        "nonconformity", "recurrence", "analyze",
        "Recurrence analysis: group NCs by product, problem tag, status "
        "or customer — verifiable counts labeled CALCULATED, never "
        "recomputed official indicators.",
        "analysis",
        fields=("group_by",) + _NC_LIST_FIELDS,
        notes=(
            "Result is CALCULATED from a bounded sample of official "
            "records; coverage (analyzed vs total) is always reported.",
        ),
    ),
    _a(
        "lmp", "performance", "analyze",
        "LMP performance briefing: official summary + goal context + "
        "NC streak, each fact labeled OBSERVED; goal comparisons "
        "labeled CALCULATED.",
        "analysis",
        fields=_LMP_PERIOD_FIELDS,
    ),
    # --- knowledge ----------------------------------------------------------
    _a(
        "nonconformity", "guide", "knowledge",
        "Versioned Engineering guidance on the nonconformity contract: "
        "fields, statuses, tags, import semantics and governance.",
        "read",
    ),
    _a(
        "lmp", "guide", "knowledge",
        "Versioned Engineering guidance on LMP domain concepts and "
        "indicator semantics.",
        "read",
    ),
    _a(
        "eva", "usage", "knowledge",
        "How to operate EVA: tools, phases, confirmation model and "
        "availability semantics.",
        "read",
    ),
    # --- execute --------------------------------------------------------------
    _a(
        "nonconformity", "create", "execute",
        "Create a nonconformity via the official contract — direct "
        "execution when the request is unambiguous; idempotency_key "
        "supported; phase=prepare validates without side effects.",
        "moderate",
        phases=("act", "prepare"),
        fields=_NC_WRITE_FIELDS,
        notes=(
            "Direct ACT: no redundant confirmation when intent, data "
            "and authorization are unequivocal.",
        ),
    ),
    _a(
        "nonconformity", "update", "execute",
        "Update a nonconformity — safe full-replace merge of `changes` "
        "over the current record with optimistic locking "
        "(expected_version = updated_at of the record you read).",
        "moderate",
        phases=("act", "prepare"),
        ref_arg="record_id",
        requires=("changes",),
        fields=_NC_WRITE_FIELDS,
        notes=(
            "Never sends a partial payload that would erase fields: "
            "the bridge merges current + changes and rejects keys "
            "outside the contract.",
        ),
    ),
    _a(
        "nonconformity", "import", "execute",
        "JSON import — destructive replace-all semantics. phase=prepare "
        "runs a dry-run report and seals a proposal; phase=commit "
        "requires the sealed proposal_ref and still honors the owner "
        "environment gate (ENG_NC_IMPORT_REPLACE_ENABLED).",
        "destructive",
        destructive=True,
        phases=("prepare", "commit"),
        requires=("items",),
        notes=(
            "No direct phase=act — replace-all always goes through a "
            "sealed proposal verified server-side.",
        ),
    ),
    # --- delete -----------------------------------------------------------------
    _a(
        "nonconformity", "delete", "delete",
        "Hard-delete a nonconformity and its history (irreversible). "
        "phase=prepare seals target + impact into a proposal; "
        "phase=commit executes only with the exact proposal_ref after "
        "verifiable human confirmation.",
        "destructive",
        destructive=True,
        phases=("prepare", "commit"),
        ref_arg="record_id",
        notes=(
            "confirmed=true from the model is NOT proof of "
            "confirmation — the sealed proposal handle is.",
        ),
    ),
)

_ACTION_INDEX: dict[tuple[str, str], SemanticAction] = {
    (a.entity, a.action): a for a in SEMANTIC_ACTIONS
}


def semantic_action(entity: str, action: str) -> SemanticAction | None:
    return _ACTION_INDEX.get((entity, action))


def actions_for_tool(tool: str) -> tuple[SemanticAction, ...]:
    return tuple(a for a in SEMANTIC_ACTIONS if a.tool == tool)


def actions_for_entity(entity: str) -> tuple[SemanticAction, ...]:
    return tuple(a for a in SEMANTIC_ACTIONS if a.entity == entity)


def entities_summary() -> list[dict]:
    entities: dict[str, list[SemanticAction]] = {}
    for action in SEMANTIC_ACTIONS:
        entities.setdefault(action.entity, []).append(action)
    return [
        {
            "entity": entity,
            "actions": sorted(a.action for a in items),
            "proven": sum(1 for a in items if a.status == "proven"),
            "total": len(items),
        }
        for entity, items in sorted(entities.items())
    ]


def unknown_action_error(entity: str, action: str) -> dict:
    """Honest typed error payload for unregistered (entity, action)."""
    allowed = sorted(
        a.action for a in actions_for_entity(entity)
    ) or sorted({a.entity for a in SEMANTIC_ACTIONS})
    return {
        "error_kind": "validation",
        "entity": entity,
        "action": action,
        "allowed": allowed,
    }


# PLANNED extension surface (Plan 54 §5) — catalogued, never executable.
PLANNED_SEMANTIC_ACTIONS: tuple[dict, ...] = (
    {
        "entity": "drawing", "action": "detail", "tool": "read",
        "status": "not_implemented",
        "note": "Desenhos técnicos — sem fonte/contrato oficial ainda.",
    },
    {
        "entity": "product", "action": "bom", "tool": "read",
        "status": "planned",
        "note": "BOM completa — parcial em product.structure; contrato "
                "dedicado ainda não existe.",
    },
    {
        "entity": "routing", "action": "steps", "tool": "read",
        "status": "not_implemented",
        "note": "Roteiros de fabricação — sem contrato oficial.",
    },
    {
        "entity": "raw_material", "action": "specification",
        "tool": "read", "status": "not_implemented",
        "note": "Matérias-primas/especificações — sem fonte oficial.",
    },
    {
        "entity": "inspection", "action": "report", "tool": "read",
        "status": "not_implemented",
        "note": "Inspeções — sem contrato oficial.",
    },
    {
        "entity": "technical_document", "action": "prepare_draft",
        "tool": "execute", "status": "planned",
        "note": "Documentos candidatos DRAFT → revisão → publicação "
                "pelo owner técnico; nunca publicação direta.",
    },
)
