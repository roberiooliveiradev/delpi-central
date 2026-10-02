"""Semantic errors for the specialist interoperability boundary.

Raw transport/protocol/library exceptions never cross Infrastructure —
they are normalized into these codes (spec 60 failure contract).
"""

from __future__ import annotations


SPECIALIST_NOT_CONFIGURED = "specialist_not_configured"
SPECIALIST_DISABLED = "specialist_disabled"
UNKNOWN_SPECIALIST = "unknown_specialist"
UNKNOWN_CAPABILITY = "unknown_capability"
MCP_UNAVAILABLE = "mcp_unavailable"
MCP_TIMEOUT = "mcp_timeout"
MCP_PROTOCOL_ERROR = "mcp_protocol_error"
MCP_INVALID_RESPONSE = "mcp_invalid_response"
MCP_RESULT_TOO_LARGE = "mcp_result_too_large"
MCP_AUTHENTICATION_FAILED = "mcp_authentication_failed"
MCP_AUTHORIZATION_DENIED = "mcp_authorization_denied"
CAPABILITY_NOT_ALLOWED_IN_PHASE = "capability_not_allowed_in_phase"


class SpecialistInteropError(Exception):
    """Bounded semantic error; never carries secrets or raw wire internals."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")
