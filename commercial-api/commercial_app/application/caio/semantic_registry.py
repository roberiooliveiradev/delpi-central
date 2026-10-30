"""CAIO semantic action registry — typed allowlist.

Pure-data model, no transport/framework imports: the six public MCP
tools dispatch on ``(entity, action)`` — never on URLs, HTTP methods,
SQL or model-supplied function names. New Commercial capabilities are
added here as registry entries, never as new MCP tools.

Classification legend (``risk``):
- ``read``        — official facts, no side effects;
- ``analysis``    — derived, labeled computation over official facts;
- ``moderate``    — non-destructive mutation (create/update);
- ``destructive`` — delete / replace — sealed proposal only.

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


_PORTFOLIO_SELECTOR_FIELDS = ("portfolio_id", "seller_id")
_SCOPE_FIELDS = _PORTFOLIO_SELECTOR_FIELDS + ("scope_mode",)
_ANALYTICS_PERIOD_FIELDS = (
    "start_date",
    "end_date",
    "branch",
    "customer_segment",
    "customer_centers",
    "customer_codes",
)

SEMANTIC_ACTIONS: tuple[SemanticAction, ...] = (
    # --- get_context ------------------------------------------------------
    _a(
        "catalog", "capabilities", "get_context",
        "Live capability discovery: entities, actions, schemas, risk, "
        "phases and honest availability — call before any other tool.",
        "read",
    ),
    # --- read: portfolio ----------------------------------------------------
    _a(
        "portfolio", "me", "read",
        "Caller commercial context: portfolios the authenticated user "
        "belongs to, membership capabilities and admin flags — official "
        "seller-portfolio contract.",
        "read",
    ),
    # --- read: customer -----------------------------------------------------
    _a(
        "customer", "list", "read",
        "Authorized customers in the caller's portfolio scope with "
        "open-order metrics — official in-scope contract.",
        "read",
        fields=_PORTFOLIO_SELECTOR_FIELDS,
    ),
    # --- read: open_order ---------------------------------------------------
    _a(
        "open_order", "list", "read",
        "Authorized open sales orders of the caller's portfolio scope.",
        "read",
        fields=_PORTFOLIO_SELECTOR_FIELDS + ("customer_centers",),
    ),
    _a(
        "open_order", "recently_closed", "read",
        "Sales orders closed in the last N days (1-90) within the "
        "caller-authorized scope.",
        "read",
        fields=_PORTFOLIO_SELECTOR_FIELDS + ("days", "customer_centers"),
    ),
    # --- read: proposal -----------------------------------------------------
    _a(
        "proposal", "list", "read",
        "Commercial proposal documents — backend search over the full "
        "eligible catalog (search, sort_by/sort_dir, pagination).",
        "read",
        fields=("search", "sort_by", "sort_dir"),
    ),
    # --- analyze ------------------------------------------------------------
    _a(
        "portfolio", "open_summary", "analyze",
        "Open-portfolio KPI summary (current open balance, no items) — "
        "official composition, never recalculated.",
        "analysis",
        fields=_SCOPE_FIELDS + ("customer_codes",),
    ),
    _a(
        "portfolio", "open_horizon", "analyze",
        "Open-portfolio horizon buckets by delivery date — official "
        "composition, never recalculated.",
        "analysis",
        fields=_SCOPE_FIELDS + ("customer_codes",),
    ),
    _a(
        "rol", "summary", "analyze",
        "ROL (receita) official summary for the period — delegated to "
        "the commercial analytics owner with the caller's scope.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS,
    ),
    # --- knowledge ----------------------------------------------------------
    _a(
        "caio", "usage", "knowledge",
        "How to operate the CAIO semantic surface: discovery, "
        "operations, confirmation model and honest states.",
        "read",
    ),
    _a(
        "commercial", "glossary", "knowledge",
        "Commercial concepts — portfolio/membership/scope, open "
        "orders, proposals, ROL — owner-authorized guidance.",
        "read",
    ),
    # --- execute (deny-by-default MVP) --------------------------------------
    _a(
        "portfolio", "create", "execute",
        "Create seller portfolio — governed write contract exists "
        "(commercial.manage); MCP write path not activated in v1.",
        "moderate",
        status="not_implemented",
        notes=("Blocked until owner-approved MCP write contract.",),
    ),
    _a(
        "portfolio", "update", "execute",
        "Update seller portfolio metadata — governed write contract "
        "exists; MCP write path not activated in v1.",
        "moderate",
        status="not_implemented",
        notes=("Blocked until owner-approved MCP write contract.",),
    ),
    _a(
        "portfolio", "manage_customers", "execute",
        "Add/transfer/replace customers in a portfolio — governed "
        "write contract exists; MCP write path not activated in v1.",
        "moderate",
        status="not_implemented",
        notes=("Blocked until owner-approved MCP write contract.",),
    ),
    # --- delete (deny-by-default MVP) ---------------------------------------
    _a(
        "portfolio", "delete", "delete",
        "Delete a seller portfolio — destructive; would require sealed "
        "proposal prepare→commit once the contract is activated.",
        "destructive",
        status="not_implemented",
        destructive=True,
        notes=("Blocked until owner-approved MCP write contract.",),
    ),
)

PLANNED_SEMANTIC_ACTIONS: tuple[str, ...] = tuple(
    a.capability for a in SEMANTIC_ACTIONS if a.status != "proven"
)


def semantic_action(entity: str, action: str) -> SemanticAction | None:
    for entry in SEMANTIC_ACTIONS:
        if entry.entity == entity and entry.action == action:
            return entry
    return None


def actions_for_entity(entity: str) -> tuple[SemanticAction, ...]:
    return tuple(a for a in SEMANTIC_ACTIONS if a.entity == entity)


def entities_summary() -> list[dict]:
    out: dict[str, dict] = {}
    for entry in SEMANTIC_ACTIONS:
        bucket = out.setdefault(
            entry.entity,
            {"entity": entry.entity, "actions": []},
        )
        bucket["actions"].append(entry.action)
    return list(out.values())
