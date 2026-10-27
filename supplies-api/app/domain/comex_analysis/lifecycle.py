"""NCM homologation lifecycle — the single source for status transitions.

States (frozen contract, no extra states):
    candidate → pending_fiscal_review → approved | rejected
    approved → inactive
    inactive | rejected → pending_fiscal_review (re-review / resubmit)

Authority split (two-code RBAC — see S0 decision):
    ``supplies.access`` — create requests and submit/resubmit for
    fiscal review;
    ``supplies.manage`` — decide (approve/reject) and deactivate.
    Approving requires the manage capability, which stands for the
    homologating authority; the fiscal-review step is tracked by audit
    events and notes, not by a separate permission code.
"""

from __future__ import annotations

STATUSES = (
    "candidate",
    "pending_fiscal_review",
    "approved",
    "rejected",
    "inactive",
)

# (from_status, to_status) → required capability: "access" or "manage"
_TRANSITIONS: dict[tuple[str, str], str] = {
    ("candidate", "pending_fiscal_review"): "access",
    ("pending_fiscal_review", "approved"): "manage",
    ("pending_fiscal_review", "rejected"): "manage",
    ("approved", "inactive"): "manage",
    ("inactive", "pending_fiscal_review"): "manage",
    ("rejected", "pending_fiscal_review"): "access",
}


class GovernanceTransitionError(RuntimeError):
    def __init__(self, message: str, *, code: str = "invalid_transition"):
        self.code = code
        super().__init__(message)


def required_capability(from_status: str, to_status: str) -> str:
    """Return 'access' | 'manage' or raise for an illegal transition."""
    capability = _TRANSITIONS.get((from_status, to_status))
    if capability is None:
        raise GovernanceTransitionError(
            f"transition {from_status} → {to_status} is not allowed"
        )
    return capability
