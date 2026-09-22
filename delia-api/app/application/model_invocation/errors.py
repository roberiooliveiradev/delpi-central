"""Provider-neutral model invocation errors.

Codes are semantic. Raw provider/SDK exceptions must not leak above infrastructure.
"""

from __future__ import annotations


class ModelInvocationError(Exception):
    """Bounded application error for model invocation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


INVALID_REQUEST = "invalid_request"
UNSUPPORTED_MODEL = "unsupported_model"
PROVIDER_UNAVAILABLE = "provider_unavailable"
TIMEOUT = "timeout"
PROVIDER_REJECTED = "provider_rejected"
INVALID_STRUCTURED_OUTPUT = "invalid_structured_output"
POLICY_EXPOSURE_DENIED = "policy_exposure_denied"
EVALUATION_FAILED = "evaluation_failed"
