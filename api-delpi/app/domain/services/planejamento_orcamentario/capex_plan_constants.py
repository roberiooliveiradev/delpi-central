"""Constantes do planejamento CAPEX por centro de custo (Fase 2C.1)."""

from __future__ import annotations

ENTITY_TYPE_CAPEX_PLAN = "capex_plan"

STATUS_DRAFT = "draft"
STATUS_SUBMITTED = "submitted"
STATUS_CHANGES_REQUESTED = "changes_requested"
STATUS_REJECTED = "rejected"
STATUS_APPROVED = "approved"

ALLOWED_PLAN_STATUSES = frozenset(
    {
        STATUS_DRAFT,
        STATUS_SUBMITTED,
        STATUS_CHANGES_REQUESTED,
        STATUS_REJECTED,
        STATUS_APPROVED,
    }
)

# Mutação de investimentos/anexos permitida nestes estados (ou plano inexistente).
EDITABLE_PLAN_STATUSES = frozenset({STATUS_DRAFT, STATUS_CHANGES_REQUESTED})

# Transições válidas: (from, action) -> to
PLAN_TRANSITIONS: dict[tuple[str, str], str] = {
    (STATUS_DRAFT, "submit"): STATUS_SUBMITTED,
    (STATUS_CHANGES_REQUESTED, "submit"): STATUS_SUBMITTED,
    (STATUS_SUBMITTED, "request_changes"): STATUS_CHANGES_REQUESTED,
    (STATUS_SUBMITTED, "reject"): STATUS_REJECTED,
    (STATUS_SUBMITTED, "approve"): STATUS_APPROVED,
}

HISTORY_ACTION_CREATED = "created"
HISTORY_ACTION_SUBMITTED = "submitted"
HISTORY_ACTION_REQUEST_CHANGES = "request_changes"
HISTORY_ACTION_REJECTED = "rejected"
HISTORY_ACTION_APPROVED = "approved"
HISTORY_ACTION_INVESTMENT_APPROVED = "investment_approved"
HISTORY_ACTION_INVESTMENT_REJECTED = "investment_rejected"

AUDIT_PLAN_CREATED = "capex_plan.created"
AUDIT_PLAN_SUBMITTED = "capex_plan.submitted"
AUDIT_PLAN_REQUEST_CHANGES = "capex_plan.request_changes"
AUDIT_PLAN_REJECTED = "capex_plan.rejected"
AUDIT_PLAN_APPROVED = "capex_plan.approved"
AUDIT_PLAN_VERSION_CONFLICT = "capex_plan.version_conflict"
AUDIT_INVESTMENT_APPROVED = "capex_investment.approved"
AUDIT_INVESTMENT_REJECTED = "capex_investment.rejected"
