"""Status canônicos da auditoria 5S operacional."""

from __future__ import annotations

AUDIT_STATUS_DRAFT = "draft"
AUDIT_STATUS_EVALUATION_COMPLETE = "evaluation_complete"
AUDIT_STATUS_NC_IN_PROGRESS = "nc_in_progress"
AUDIT_STATUS_CLOSED = "closed"
AUDIT_STATUS_CLOSED_WITHOUT_NC_TREATMENT = "closed_without_nc_treatment"

AUDIT_CLOSED_STATUSES = frozenset(
    {
        AUDIT_STATUS_CLOSED,
        AUDIT_STATUS_CLOSED_WITHOUT_NC_TREATMENT,
    }
)

AUDIT_FORCE_CLOSE_UNTREATED_SOURCE_STATUSES = frozenset(
    {
        AUDIT_STATUS_EVALUATION_COMPLETE,
        AUDIT_STATUS_NC_IN_PROGRESS,
    }
)

AUDIT_ALL_STATUSES = frozenset(
    {
        AUDIT_STATUS_DRAFT,
        AUDIT_STATUS_EVALUATION_COMPLETE,
        AUDIT_STATUS_NC_IN_PROGRESS,
        AUDIT_STATUS_CLOSED,
        AUDIT_STATUS_CLOSED_WITHOUT_NC_TREATMENT,
    }
)


def is_audit_closed(status: str | None) -> bool:
    return str(status or "") in AUDIT_CLOSED_STATUSES
