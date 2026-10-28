"""DAVI dynamic READ application errors (transport-agnostic)."""

from __future__ import annotations

# Owner-published typed error vocabulary for the MCP wire
# (structuredContent.code). DELIA-C3-DAVI-EXCLUSIVE-COMPLETION-01:
# generic VALIDATION_ERROR was ambiguous — it covered argument
# rejections, eligibility denials and owner execution failures, so
# consumers could not classify repairability by contract. Each class
# now carries its own code; only ARGUMENT_VALIDATION is argument-
# repairable, and only when recoverable is explicitly true.
ARGUMENT_VALIDATION_CODE = "ARGUMENT_VALIDATION"
CAPABILITY_NOT_ALLOWED_CODE = "CAPABILITY_NOT_ALLOWED"
OWNER_EXECUTION_ERROR_CODE = "OWNER_EXECUTION_ERROR"
AUTHENTICATION_REQUIRED_CODE = "AUTHENTICATION_REQUIRED"
AUTHORIZATION_DENIED_CODE = "AUTHORIZATION_DENIED"


class GovernedExecutionError(RuntimeError):
    """Rejected or failed governed execution (no HTTP semantics).

    ``code`` carries the owner-typed wire classification; the
    interface layer projects it verbatim into structuredContent.code.
    """

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.code = code
