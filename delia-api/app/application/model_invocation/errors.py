"""Provider-neutral model invocation errors.

Codes are semantic. Raw provider/SDK exceptions must not leak above infrastructure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.model_invocation.contracts import (
        ContextBudgetObservation,
    )


class ModelInvocationError(Exception):
    """Bounded application error for model invocation."""

    def __init__(
        self,
        code: str,
        message: str,
        context_budget: ContextBudgetObservation | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        # Pre-call budget decision when the invocation was rejected for
        # exceeding the declared context window (CONTEXT_TOO_LARGE).
        self.context_budget = context_budget


INVALID_REQUEST = "invalid_request"
UNSUPPORTED_MODEL = "unsupported_model"
PROVIDER_UNAVAILABLE = "provider_unavailable"
TIMEOUT = "timeout"
PROVIDER_REJECTED = "provider_rejected"
INVALID_STRUCTURED_OUTPUT = "invalid_structured_output"
POLICY_EXPOSURE_DENIED = "policy_exposure_denied"
CONTEXT_TOO_LARGE = "context_too_large"
EVALUATION_FAILED = "evaluation_failed"
