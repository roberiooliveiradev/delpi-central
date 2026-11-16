"""Governed-write error codes for the DAVI semantic execute surface.

Transport-agnostic: the MCP bridge maps ``code``/``status_code`` into the
stable typed tool-result contract; owner (Strategic Indicators) HTTP
semantics are preserved — a deterministic owner rejection is never
reported as service unavailability.
"""

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


# Stable public codes (same vocabulary as sibling governed-write stacks).
CAPABILITY_NOT_ALLOWED = "capability_not_allowed"
CONFIRMATION_REQUIRED = "confirmation_required"
PROPOSAL_REQUIRED = "proposal_required"
PROPOSAL_NOT_FOUND = "proposal_not_found"
PROPOSAL_EXPIRED = "proposal_expired"
PROPOSAL_STALE = "proposal_stale"
PROPOSAL_MISMATCH = "proposal_mismatch"
PROPOSAL_ACTOR_MISMATCH = "proposal_actor_mismatch"
OUTCOME_VERIFICATION_FAILED = "outcome_verification_failed"
UNKNOWN_RESULT = "unknown_result"
FORBIDDEN = "forbidden"
VALIDATION = "validation"
NOT_FOUND = "not_found"
CONFLICT = "conflict"
UNAUTHENTICATED = "unauthenticated"
OWNER_UNAVAILABLE = "owner_unavailable"
INTERNAL = "internal"
