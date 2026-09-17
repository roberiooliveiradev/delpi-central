"""Governed-write error codes (transport-agnostic)."""

from __future__ import annotations


class GovernedWriteError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int = 400,
        data: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.data = data or {}


# Stable public codes
PROPOSAL_REQUIRED = "proposal_required"
PROPOSAL_NOT_FOUND = "proposal_not_found"
PROPOSAL_EXPIRED = "proposal_expired"
PROPOSAL_STALE = "proposal_stale"
PROPOSAL_MISMATCH = "proposal_mismatch"
PROPOSAL_ACTOR_MISMATCH = "proposal_actor_mismatch"
OUTCOME_VERIFICATION_FAILED = "outcome_verification_failed"
FORBIDDEN = "forbidden"
VALIDATION = "validation"
NOT_FOUND = "not_found"
CONFLICT = "conflict"
BUSINESS_RULE = "business_rule"
UNAUTHENTICATED = "unauthenticated"
INTERNAL = "internal"
