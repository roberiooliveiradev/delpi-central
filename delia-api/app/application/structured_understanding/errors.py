"""Bounded application errors for Structured Understanding."""

from __future__ import annotations


class StructuredUnderstandingError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


INVALID_REQUEST = "invalid_request"
INVALID_STRUCTURED_RESULT = "invalid_structured_result"
UNSUPPORTED_SCHEMA = "unsupported_schema"
EPISTEMIC_VIOLATION = "epistemic_violation"
FORBIDDEN_RESULT_FIELD = "forbidden_result_field"
