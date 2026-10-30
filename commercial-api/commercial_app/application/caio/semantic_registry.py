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

``requires`` documents the backend permission family re-checked on
every call — it never grants authorization by itself.

Parity coverage: registry entries implement the eligible operations
of the Portal Comercial inventory; binary/realtime/internal
operations are excluded per CAIO_2_PARITY_EXECUTION_TRAIL E1
(NOT_SEMANTICALLY_ELIGIBLE — see CAIO_PARITY_MATRIX.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field

SEMANTIC_CATALOG_VERSION = "2.0"

SEMANTIC_TOOL_NAMES: tuple[str, ...] = (
    "get_context",
    "read",
    "analyze",
    "knowledge",
    "execute",
    "delete",
)

# Permission families — documentation only; the effective check is the
# official one in commercial_permissions + route-equivalent gates.
REQ_READ = "commercial.read"
REQ_MANAGE = "commercial.manage"
REQ_ANALYTICS = "commercial.analytics"
REQ_FOLLOWUPS = "commercial.followups"
REQ_WORKLIST = "commercial.worklist"
REQ_ACCESS = "commercial.access"
REQ_AUDIT = "commercial.audit"
REQ_PROPOSALS = "commercial.proposals.view"
REQ_BILLING_SHARE = "commercial.portfolio_billing_share"


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
_CUSTOMER_PAIR_FIELDS = ("customer_code", "customer_store")
_DELETE_PHASES = ("prepare", "commit")

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
        requires=(REQ_READ,),
    ),
    _a(
        "portfolio", "get", "read",
        "Seller portfolio detail — members see their own portfolio; "
        "manage sees any.",
        "read",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        requires=(REQ_READ,),
    ),
    _a(
        "portfolio", "list", "read",
        "Seller portfolios — manage/team scope lists all; members are "
        "restricted to portfolio.me.",
        "read",
        fields=("active_only", "include_customers"),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "audit", "read",
        "Portfolio audit timeline (members, owner, transfers, active "
        "flag) — official audit_log read.",
        "read",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        fields=("page", "page_size"),
        requires=(REQ_READ, REQ_AUDIT),
    ),
    _a(
        "portfolio", "coverage_audit", "read",
        "Customer coverage audit across portfolios — manage only.",
        "read",
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "load_summary", "read",
        "Load KPIs per portfolio/person — manage only.",
        "read",
        fields=("active_only",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "customer_coverage", "read",
        "Shared-coverage lookup: which batch customers sit in 2+ "
        "portfolios of the authorized scope.",
        "read",
        fields=("customers", "portfolio_ids"),
        requires=(REQ_READ,),
    ),
    # --- read: customer -----------------------------------------------------
    _a(
        "customer", "list", "read",
        "Authorized customers in the caller's portfolio scope with "
        "open-order metrics — official in-scope contract.",
        "read",
        fields=_PORTFOLIO_SELECTOR_FIELDS,
        requires=(REQ_READ,),
    ),
    _a(
        "customer", "search", "read",
        "Active-customer search over the production catalog "
        "(backend search + pagination).",
        "read",
        fields=("q", "include_blocked", "page", "page_size"),
        requires=(REQ_READ,),
    ),
    _a(
        "customer", "enrichment", "read",
        "Batch enrichment of scoped customers (trend window, billing "
        "nature) — same customer pairs never exceed caller scope.",
        "read",
        fields=("customers", "window_days", "nature"),
        requires=(REQ_READ,),
    ),
    _a(
        "customer", "billing_series", "read",
        "Customer billing series (monthly points per customer pair "
        "of the authorized scope).",
        "read",
        fields=(
            "customers", "months", "start_date", "end_date",
            "granularity", "nature", "metric", "product_codes",
            "product_groups", "market", "customer_centers",
        ),
        requires=(REQ_READ,),
    ),
    _a(
        "customer", "center_assignments", "read",
        "Customer center assignments (SA7) for the scoped pairs.",
        "read",
        fields=("customers",),
        requires=(REQ_READ,),
    ),
    _a(
        "customer", "outbound_invoices", "read",
        "Outbound invoices of one customer account (account 360 — "
        "single pair, no membership filter).",
        "read",
        fields=_CUSTOMER_PAIR_FIELDS + (
            "branch", "start_date", "end_date", "page", "page_size",
        ),
        requires=(REQ_READ,),
    ),
    _a(
        "customer", "outbound_invoice", "read",
        "Single outbound invoice detail of a customer account.",
        "read",
        fields=_CUSTOMER_PAIR_FIELDS + (
            "branch", "invoice_number", "invoice_series",
        ),
        requires=(REQ_READ,),
    ),
    _a(
        "customer", "open_orders", "read",
        "Open orders of one customer account (account 360).",
        "read",
        fields=_CUSTOMER_PAIR_FIELDS + ("branch",),
        requires=(REQ_READ,),
    ),
    _a(
        "customer", "contacts", "read",
        "Contacts bundle of one customer account (account 360).",
        "read",
        fields=_CUSTOMER_PAIR_FIELDS,
        requires=(REQ_READ,),
    ),
    _a(
        "customer", "account_audit", "read",
        "Account audit timeline of one customer account.",
        "read",
        fields=_CUSTOMER_PAIR_FIELDS + ("limit", "page", "page_size"),
        requires=(REQ_READ,),
    ),
    # --- read: customer_center -------------------------------------------------
    _a(
        "customer_center", "list", "read",
        "Distinct customer centers (SA7) of the analytics scope.",
        "read",
        fields=_PORTFOLIO_SELECTOR_FIELDS + ("scope_mode",),
        requires=(REQ_ANALYTICS,),
    ),
    # --- read: open_order ---------------------------------------------------
    _a(
        "open_order", "list", "read",
        "Authorized open sales orders of the caller's portfolio scope.",
        "read",
        fields=_PORTFOLIO_SELECTOR_FIELDS + ("customer_centers",),
        requires=(REQ_READ,),
    ),
    _a(
        "open_order", "recently_closed", "read",
        "Sales orders closed in the last N days (1-90) within the "
        "caller-authorized scope.",
        "read",
        fields=_PORTFOLIO_SELECTOR_FIELDS + ("days", "customer_centers"),
        requires=(REQ_READ,),
    ),
    _a(
        "open_order", "open_ops", "read",
        "Open production orders (OPs abertas) — production catalog "
        "passthrough, no portfolio filter.",
        "read",
        requires=(REQ_READ,),
    ),
    # --- read: proposal -----------------------------------------------------
    _a(
        "proposal", "list", "read",
        "Commercial proposal documents — backend search over the full "
        "eligible catalog (search, sort_by/sort_dir, pagination).",
        "read",
        fields=("search", "sort_by", "sort_dir", "page", "page_size"),
        requires=(REQ_PROPOSALS,),
    ),
    _a(
        "proposal", "get", "read",
        "Single proposal document detail by internal proposal number.",
        "read",
        ref_arg="proposta_interna",
        ref_description="Internal proposal number (proposta_interna).",
        requires=(REQ_PROPOSALS,),
    ),
    _a(
        "proposal", "analytics_list", "read",
        "Proposals analytics listing (TOTVS) — period, status and "
        "scope filters; analytics permission.",
        "read",
        fields=_SCOPE_FIELDS + (
            "start_date", "end_date", "branch", "customer_segment",
            "granularity", "status", "search", "product_code",
            "product_group", "sort_by", "sort_dir",
            "account_customer_code", "customer_codes",
            "page", "page_size",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "proposal", "analytics_get", "read",
        "Single TOTVS proposal detail (analytics contract).",
        "read",
        ref_arg="proposal_number",
        ref_description="TOTVS proposal number.",
        fields=_SCOPE_FIELDS,
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "proposal", "history_events", "read",
        "Proposal history events timeline (analytics contract).",
        "read",
        ref_arg="proposal_number",
        ref_description="TOTVS proposal number.",
        fields=_SCOPE_FIELDS,
        requires=(REQ_ANALYTICS,),
    ),
    # --- read: worklist / tasks / activities ---------------------------------
    _a(
        "worklist", "mine", "read",
        "Caller worklist queue — scope=mine|team (team requires "
        "worklist.team.view or manage).",
        "read",
        fields=("scope", "assignee_user_id"),
        requires=(REQ_WORKLIST,),
    ),
    _a(
        "worklist", "done", "read",
        "Recently completed worklist items.",
        "read",
        fields=("scope", "assignee_user_id", "limit"),
        requires=(REQ_WORKLIST,),
    ),
    _a(
        "task", "list", "read",
        "Caller tasks by status (open default).",
        "read",
        fields=("status",),
        requires=(REQ_WORKLIST,),
    ),
    _a(
        "activity", "list", "read",
        "Commercial activities timeline of a customer account.",
        "read",
        fields=_CUSTOMER_PAIR_FIELDS + ("limit",),
        requires=(REQ_READ,),
    ),
    # --- read: groups / settings / favorites / roster / attachments -----------
    _a(
        "group", "list", "read",
        "Commercial groups (operational teams) — manage only.",
        "read",
        fields=("active_only",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "group", "get", "read",
        "Single commercial group with members — manage only.",
        "read",
        ref_arg="group_id",
        ref_description="Group UUID.",
        requires=(REQ_MANAGE,),
    ),
    _a(
        "sla_policy", "list", "read",
        "SLA policies — include_inactive requires manage.",
        "read",
        fields=("include_inactive",),
        requires=(REQ_READ,),
    ),
    _a(
        "home_favorite", "list", "read",
        "Caller home favorites.",
        "read",
        requires=(REQ_READ,),
    ),
    _a(
        "team", "roster", "read",
        "Commercial team roster — manage only.",
        "read",
        requires=(REQ_MANAGE,),
    ),
    _a(
        "attachment", "list", "read",
        "Attachment metadata of an owner entity (task/activity/room "
        "message) — bytes are served only by the Portal route.",
        "read",
        fields=("owner_type", "owner_id"),
        requires=(REQ_READ, REQ_FOLLOWUPS),
    ),
    # --- read: interaction rooms ----------------------------------------------
    _a(
        "interaction_room", "list", "read",
        "Caller interaction-room inbox.",
        "read",
        fields=("filter_key", "query", "limit", "cursor"),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "get", "read",
        "Interaction room detail for a member.",
        "read",
        ref_arg="room_id",
        ref_description="Room UUID.",
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "members", "read",
        "Members of an interaction room (member-scoped).",
        "read",
        ref_arg="room_id",
        ref_description="Room UUID.",
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "messages", "read",
        "Messages of an interaction room (member-scoped, "
        "cursor pagination).",
        "read",
        ref_arg="room_id",
        ref_description="Room UUID.",
        fields=("limit", "before_created_at", "before_id", "q"),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "shared_items", "read",
        "Shared items (orders/customers/tasks) linked in a room.",
        "read",
        ref_arg="room_id",
        ref_description="Room UUID.",
        fields=("kind",),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "pins", "read",
        "Pinned messages of a room.",
        "read",
        ref_arg="room_id",
        ref_description="Room UUID.",
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "mention_suggest", "read",
        "Mention suggestions (users/customers/groups) for a room "
        "context — never broadens the caller scope.",
        "read",
        fields=("q", "kinds", "limit"),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "entity_preview", "read",
        "Preview card of a linked entity reference.",
        "read",
        fields=("kind", "ref"),
        requires=(REQ_ACCESS,),
    ),
    # --- read: production BFF ---------------------------------------------------
    _a(
        "production", "order", "read",
        "Production order detail by OP number (production owner).",
        "read",
        ref_arg="production_order",
        ref_description="Production order (OP) number.",
        fields=("branch",),
        requires=(REQ_READ, REQ_ANALYTICS),
    ),
    _a(
        "production", "appointments", "read",
        "Production appointments by OP.",
        "read",
        fields=("op", "branch", "page", "page_size"),
        requires=(REQ_READ, REQ_ANALYTICS),
    ),
    _a(
        "production", "product_status", "read",
        "Factory status of a product (production owner).",
        "read",
        ref_arg="product_code",
        ref_description="Product code (Protheus B1_COD).",
        fields=("branch",),
        requires=(REQ_READ, REQ_ANALYTICS),
    ),
    _a(
        "production", "product_structure", "read",
        "Product structure/BOM (production owner).",
        "read",
        ref_arg="product_code",
        ref_description="Product code (Protheus B1_COD).",
        fields=("branch",),
        requires=(REQ_READ, REQ_ANALYTICS),
    ),
    # --- read: user profile ------------------------------------------------------
    _a(
        "user_profile", "get", "read",
        "Merged user profile (Portal person-profile + Commercial "
        "store).",
        "read",
        ref_arg="user_id",
        ref_description="User id (Keycloak sub).",
        requires=(REQ_READ,),
    ),
    # --- analyze ------------------------------------------------------------
    _a(
        "portfolio", "open_summary", "analyze",
        "Open-portfolio KPI summary (current open balance, no items) — "
        "official composition, never recalculated.",
        "analysis",
        fields=_SCOPE_FIELDS + ("customer_codes",),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "portfolio", "open_horizon", "analyze",
        "Open-portfolio horizon buckets by delivery date — official "
        "composition, never recalculated.",
        "analysis",
        fields=_SCOPE_FIELDS + ("customer_codes",),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "portfolio", "billing_share", "analyze",
        "Portfolio billing share of company ROL — manage/billing-share "
        "permission, official composition.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS + ("nature",),
        requires=(REQ_BILLING_SHARE,),
    ),
    _a(
        "portfolio", "billing_ranking", "analyze",
        "Customer ROL delta ranking vs prior period — official "
        "composition.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS + (
            "group_by", "limit", "order", "nature",
        ),
        requires=(REQ_READ, REQ_MANAGE, REQ_ANALYTICS, REQ_BILLING_SHARE),
    ),
    _a(
        "rol", "summary", "analyze",
        "ROL (receita) official summary for the period — delegated to "
        "the commercial analytics owner with the caller's scope.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS,
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "rol", "series", "analyze",
        "ROL time series by granularity.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS + ("granularity",),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "rol", "by_product", "analyze",
        "ROL grouped by product/family/market.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS + (
            "product_codes", "product_groups", "market", "group_by",
            "limit",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "rol", "by_customer", "analyze",
        "ROL grouped by customer (ranking + include_others).",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS + (
            "product_codes", "product_groups", "market", "limit",
            "include_others",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "billing", "by_customer_month", "analyze",
        "Billing grouped by customer and month.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS + (
            "nature", "limit",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "closing_rate", "summary", "analyze",
        "Sales conversion/closing rate KPI.",
        "analysis",
        fields=_SCOPE_FIELDS + (
            "start_date", "end_date", "branch", "customer_segment",
            "customer_codes",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "closing_rate", "series", "analyze",
        "Closing-rate time series.",
        "analysis",
        fields=_SCOPE_FIELDS + (
            "start_date", "end_date", "branch", "customer_segment",
            "customer_codes",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "sales_order_otd", "summary", "analyze",
        "On-time-delivery KPI of sales orders.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS,
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "sales_order_otd", "panel", "analyze",
        "OTD panel with per-order rows.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS,
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "sales_order_otd", "series", "analyze",
        "OTD time series.",
        "analysis",
        fields=_SCOPE_FIELDS + _ANALYTICS_PERIOD_FIELDS,
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "sales_order_otd", "line_detail", "analyze",
        "OTD detail of one sales-order line.",
        "analysis",
        fields=_SCOPE_FIELDS + (
            "branch", "order_number", "line_item", "customer_centers",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "new_business", "rol_pct", "analyze",
        "New-business share of ROL.",
        "analysis",
        fields=_SCOPE_FIELDS + (
            "start_date", "end_date", "branch", "customer_segment",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "new_business", "rol_target_pct", "analyze",
        "New-business ROL target percentage.",
        "analysis",
        fields=_SCOPE_FIELDS + (
            "start_date", "end_date", "branch", "customer_segment",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "weg", "rol_target_pct", "analyze",
        "WEG ROL target percentage.",
        "analysis",
        fields=_SCOPE_FIELDS + (
            "start_date", "end_date", "branch", "customer_segment",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "dashboard", "department_idd", "analyze",
        "Department IDD indicator (cross-department dashboard).",
        "analysis",
        fields=(
            "department_id", "competence", "start_date", "end_date",
            "branch",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "dashboard", "department_indicators", "analyze",
        "Department indicator set (cross-department dashboard).",
        "analysis",
        fields=(
            "department_id", "competence", "start_date", "end_date",
            "branch",
        ),
        requires=(REQ_ANALYTICS,),
    ),
    _a(
        "opportunity", "collaborator_summary", "analyze",
        "Opportunity summary grouped by collaborator.",
        "analysis",
        fields=_SCOPE_FIELDS + (
            "start_date", "end_date", "branch", "customer_segment",
        ),
        requires=(REQ_ANALYTICS,),
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
    # --- execute: portfolio (manage) -------------------------------------------
    _a(
        "portfolio", "create", "execute",
        "Create seller portfolio — official manage contract with "
        "audit trail.",
        "moderate",
        fields=(
            "user_id", "display_name", "customers", "user_ids",
            "owner_user_id",
        ),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "update", "execute",
        "Update seller portfolio name/active flag.",
        "moderate",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        fields=("display_name", "active"),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "customers_replace", "execute",
        "Replace the whole customer set of a portfolio.",
        "moderate",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        fields=("customers",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "customer_add", "execute",
        "Add one customer to a portfolio.",
        "moderate",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        fields=(
            "customer_code", "customer_store", "customer_name",
            "customer_center",
        ),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "customer_remove", "execute",
        "Remove one customer from a portfolio (membership change, "
        "not data deletion).",
        "moderate",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        fields=("customer_code", "customer_store", "customer_center"),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "members_replace", "execute",
        "Replace the member set of a portfolio.",
        "moderate",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        fields=("members",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "member_add", "execute",
        "Add a member to a portfolio.",
        "moderate",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        fields=("user_id", "role"),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "member_remove", "execute",
        "Remove a member from a portfolio.",
        "moderate",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        fields=("user_id",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "owner_set", "execute",
        "Set the owner of a portfolio.",
        "moderate",
        ref_arg="portfolio_id",
        ref_description="Portfolio UUID.",
        fields=("user_id",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "transfer", "execute",
        "Transfer customers between portfolios with reason note.",
        "moderate",
        fields=(
            "source_portfolio_id", "target_portfolio_id",
            "customers", "reason_note",
        ),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "transfer_bulk", "execute",
        "Best-effort bulk customer transfer (per-customer result).",
        "moderate",
        fields=(
            "source_portfolio_id", "target_portfolio_id",
            "customers", "reason_note",
        ),
        requires=(REQ_MANAGE,),
    ),
    # --- execute: worklist (followups) -------------------------------------------
    _a(
        "task", "create", "execute",
        "Create a follow-up task (customers, assignees, groups, due "
        "date) — same visibility rules as the Portal.",
        "moderate",
        fields=(
            "title", "description", "task_type", "priority", "due_at",
            "customer_code", "customer_store", "customers",
            "assignee_user_id", "assignee_user_ids",
            "assignee_group_ids", "related_entity_type",
            "related_entity_id", "source_interaction_message_id",
        ),
        requires=(REQ_FOLLOWUPS,),
    ),
    _a(
        "task", "update", "execute",
        "Update a task (title/priority/due/assignees).",
        "moderate",
        ref_arg="task_id",
        ref_description="Task UUID.",
        fields=(
            "title", "description", "task_type", "priority", "due_at",
            "customer_code", "customer_store", "customers",
            "assignee_user_id", "assignee_user_ids",
            "assignee_group_ids",
        ),
        requires=(REQ_FOLLOWUPS,),
    ),
    _a(
        "task", "complete", "execute",
        "Mark a task as completed.",
        "moderate",
        ref_arg="task_id",
        ref_description="Task UUID.",
        requires=(REQ_FOLLOWUPS,),
    ),
    _a(
        "task", "defer", "execute",
        "Defer a task to a new due date.",
        "moderate",
        ref_arg="task_id",
        ref_description="Task UUID.",
        fields=("due_at",),
        requires=(REQ_FOLLOWUPS,),
    ),
    _a(
        "task", "reassign", "execute",
        "Reassign a task to other users/groups.",
        "moderate",
        ref_arg="task_id",
        ref_description="Task UUID.",
        fields=(
            "assignee_user_id", "assignee_user_ids",
            "assignee_group_ids",
        ),
        requires=(REQ_FOLLOWUPS,),
    ),
    _a(
        "task", "from_message", "execute",
        "Create a task from an interaction-room message.",
        "moderate",
        fields=(
            "room_id", "message_id", "title", "due_at",
            "target_user_ids", "target_group_ids",
        ),
        requires=(REQ_ACCESS, REQ_FOLLOWUPS),
    ),
    _a(
        "activity", "create", "execute",
        "Register a commercial activity (call/visit/note) on a "
        "customer account or task.",
        "moderate",
        fields=(
            "activity_type", "subject", "body", "occurred_at",
            "customer_code", "customer_store", "task_id",
        ),
        requires=(REQ_FOLLOWUPS,),
    ),
    # --- execute: groups / sla / favorites / contacts / profile -------------------
    _a(
        "group", "create", "execute",
        "Create a commercial group — manage only.",
        "moderate",
        fields=("name", "kind", "sort_order", "user_ids"),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "group", "rename", "execute",
        "Rename a commercial group — manage only.",
        "moderate",
        ref_arg="group_id",
        ref_description="Group UUID.",
        fields=("name",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "group", "members_replace", "execute",
        "Replace group members — manage only.",
        "moderate",
        ref_arg="group_id",
        ref_description="Group UUID.",
        fields=("user_ids",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "group", "member_add", "execute",
        "Add a member to a group — manage only.",
        "moderate",
        ref_arg="group_id",
        ref_description="Group UUID.",
        fields=("user_id",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "group", "member_remove", "execute",
        "Remove a member from a group — manage only.",
        "moderate",
        ref_arg="group_id",
        ref_description="Group UUID.",
        fields=("user_id",),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "sla_policy", "create", "execute",
        "Create an SLA policy — manage only.",
        "moderate",
        fields=(
            "code", "name", "appliesTo", "durationHours",
            "calendarCode", "active",
        ),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "sla_policy", "update", "execute",
        "Update an SLA policy — manage only.",
        "moderate",
        ref_arg="policy_id",
        ref_description="SLA policy id.",
        fields=(
            "code", "name", "appliesTo", "durationHours",
            "calendarCode", "active",
        ),
        requires=(REQ_MANAGE,),
    ),
    _a(
        "home_favorite", "put", "execute",
        "Replace the caller's home favorites list.",
        "moderate",
        fields=("items",),
        requires=(REQ_READ,),
    ),
    _a(
        "contact", "create", "execute",
        "Create a contact on a customer account.",
        "moderate",
        fields=_CUSTOMER_PAIR_FIELDS + (
            "full_name", "role_title", "channel", "email",
            "phone_e164", "is_whatsapp", "is_primary", "source",
        ),
        requires=(REQ_READ, REQ_MANAGE),
    ),
    _a(
        "contact", "update", "execute",
        "Update an existing customer contact.",
        "moderate",
        ref_arg="contact_id",
        ref_description="Contact UUID.",
        fields=_CUSTOMER_PAIR_FIELDS + (
            "full_name", "role_title", "channel", "email",
            "phone_e164", "is_whatsapp", "is_primary",
        ),
        requires=(REQ_READ, REQ_MANAGE),
    ),
    _a(
        "user_profile", "update", "execute",
        "Update the caller's own profile (job title, phones).",
        "moderate",
        fields=(
            "user_id", "job_title", "phone_e164", "mobile_e164",
            "whatsapp_e164",
        ),
        requires=(REQ_READ,),
    ),
    # --- execute: interaction rooms / messages -------------------------------------
    _a(
        "interaction_room", "resolve", "execute",
        "Resolve (find-or-create) an interaction room by entity, "
        "group or DM peer.",
        "moderate",
        fields=(
            "kind", "entity_type", "entity_key", "group_id", "title",
        ),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "rename", "execute",
        "Rename an interaction room (member).",
        "moderate",
        ref_arg="room_id",
        ref_description="Room UUID.",
        fields=("title",),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "member_add", "execute",
        "Add a member to a room.",
        "moderate",
        ref_arg="room_id",
        ref_description="Room UUID.",
        fields=("user_id",),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "member_remove", "execute",
        "Remove a member from a room.",
        "moderate",
        ref_arg="room_id",
        ref_description="Room UUID.",
        fields=("user_id",),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_room", "mark_read", "execute",
        "Mark a room as read for the caller.",
        "moderate",
        ref_arg="room_id",
        ref_description="Room UUID.",
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_message", "post", "execute",
        "Post a message to an interaction room.",
        "moderate",
        ref_arg="room_id",
        ref_description="Room UUID.",
        fields=("body_text", "message_kind", "parent_id", "mentions"),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_message", "update", "execute",
        "Edit the caller's own room message.",
        "moderate",
        fields=(
            "room_id", "message_id", "body_text", "mentions",
        ),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_message", "reaction_set", "execute",
        "Set a reaction on a room message.",
        "moderate",
        fields=("room_id", "message_id", "code"),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_message", "reaction_clear", "execute",
        "Clear the caller's reaction on a room message.",
        "moderate",
        fields=("room_id", "message_id", "code"),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_message", "pin", "execute",
        "Pin a room message.",
        "moderate",
        fields=("room_id", "message_id"),
        requires=(REQ_ACCESS,),
    ),
    _a(
        "interaction_message", "unpin", "execute",
        "Unpin a room message.",
        "moderate",
        fields=("room_id", "message_id"),
        requires=(REQ_ACCESS,),
    ),
    # --- delete (sealed prepare→commit only) --------------------------------------
    _a(
        "portfolio", "deactivate", "delete",
        "Deactivate a seller portfolio (reversible soft-delete) — "
        "sealed proposal only.",
        "destructive",
        destructive=True,
        phases=_DELETE_PHASES,
        requires=(REQ_MANAGE,),
    ),
    _a(
        "portfolio", "purge", "delete",
        "Permanently purge an inactive seller portfolio — sealed "
        "proposal only.",
        "destructive",
        destructive=True,
        phases=_DELETE_PHASES,
        requires=(REQ_MANAGE,),
    ),
    _a(
        "group", "delete", "delete",
        "Delete a commercial group — sealed proposal only.",
        "destructive",
        destructive=True,
        phases=_DELETE_PHASES,
        requires=(REQ_MANAGE,),
    ),
    _a(
        "task", "delete", "delete",
        "Delete a task — sealed proposal only.",
        "destructive",
        destructive=True,
        phases=_DELETE_PHASES,
        requires=(REQ_FOLLOWUPS,),
    ),
    _a(
        "interaction_room", "delete", "delete",
        "Soft-delete an interaction room — manage only, sealed "
        "proposal.",
        "destructive",
        destructive=True,
        phases=_DELETE_PHASES,
        requires=(REQ_MANAGE,),
    ),
    _a(
        "interaction_message", "delete", "delete",
        "Soft-delete a room message — sealed proposal only.",
        "destructive",
        destructive=True,
        ref_arg="target_ref",
        ref_description=(
            "Compound ref: "
            "room_id=<uuid>&message_id=<uuid>."
        ),
        phases=_DELETE_PHASES,
        requires=(REQ_ACCESS,),
    ),
    _a(
        "contact", "delete", "delete",
        "Soft-delete a customer contact — sealed proposal only.",
        "destructive",
        destructive=True,
        ref_arg="target_ref",
        ref_description=(
            "Compound ref: contact_id=<uuid>&"
            "customer_code=<code>&customer_store=<store>."
        ),
        phases=_DELETE_PHASES,
        requires=(REQ_READ, REQ_MANAGE),
    ),
    _a(
        "sla_policy", "deactivate", "delete",
        "Deactivate an SLA policy — sealed proposal only.",
        "destructive",
        destructive=True,
        phases=_DELETE_PHASES,
        requires=(REQ_MANAGE,),
    ),
    _a(
        "attachment", "delete", "delete",
        "Delete an attachment — sealed proposal only.",
        "destructive",
        destructive=True,
        phases=_DELETE_PHASES,
        requires=(REQ_FOLLOWUPS,),
    ),
    _a(
        "user_profile", "photo_delete", "delete",
        "Delete a user profile photo — sealed proposal only; own "
        "profile or manager.",
        "destructive",
        destructive=True,
        ref_arg="target_ref",
        ref_description="Target user_id.",
        phases=_DELETE_PHASES,
        requires=(REQ_ACCESS,),
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
