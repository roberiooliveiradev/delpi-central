"""Constantes — Orçamento de Pessoal (Fase 3B.1 / 3B.1.1 / 3C.1)."""

from __future__ import annotations

ENTITY_TYPE_PERSONNEL_PLAN = "personnel_plan"
ENTITY_TYPE_PERSONNEL_PLAN_LINE = "personnel_plan_line"

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

# Mutação de linhas permitida nestes estados.
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

# Nome de cargo digitado livremente na linha (sem catálogo / sem ERP).
POSITION_NAME_MAX_LENGTH = 200

# Âncoras da planilha ORÇAMENTO PESSOAL (não mensalizar nesta fase).
# headcount_forecast = coluna "Previsto" — nomenclatura original preservada.
HEADCOUNT_FIELDS = (
    "headcount_dec_2025",  # Dez/2025
    "headcount_oct_2026",  # Out/2026
    "headcount_forecast",  # Previsto
    "headcount_dec_2027",  # Dez/2027
)

AUDIT_PLAN_RESOLVED = "personnel_plan.resolved"
AUDIT_PLAN_CREATED = "personnel_plan.created"
AUDIT_PLAN_SUBMITTED = "personnel_plan.submitted"
AUDIT_PLAN_REQUEST_CHANGES = "personnel_plan.request_changes"
AUDIT_PLAN_REJECTED = "personnel_plan.rejected"
AUDIT_PLAN_APPROVED = "personnel_plan.approved"
AUDIT_PLAN_VERSION_CONFLICT = "personnel_plan.version_conflict"

AUDIT_LINE_CREATED = "personnel_plan_line.created"
AUDIT_LINE_UPDATED = "personnel_plan_line.updated"
AUDIT_LINE_ARCHIVED = "personnel_plan_line.archived"
AUDIT_LINE_VERSION_CONFLICT = "personnel_plan_line.version_conflict"

AUDIT_ACCESS_DENIED = "personnel_plan.access_denied"
