"""Bounded semantic errors for the interactive interaction slice.

Codes are semantic and interface-agnostic. Raw SDK/HTTP exceptions must
never leak above infrastructure.
"""

from __future__ import annotations


class InteractionError(Exception):
    """Bounded application error for interactive interaction turns."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


UNAUTHENTICATED = "unauthenticated"
FORBIDDEN = "forbidden"
INVALID_REQUEST = "invalid_request"
MODEL_UNAVAILABLE = "model_unavailable"
MODEL_TIMEOUT = "model_timeout"
INVALID_MODEL_OUTPUT = "invalid_model_output"
FORBIDDEN_MODEL_OUTPUT = "forbidden_model_output"
INTERNAL_ERROR = "internal_error"
