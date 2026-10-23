"""Governed per-logical-call LLM retry policy — doc 103 PO decision.

At most three real invocations for ONE logical model call: the initial
invocation plus up to two governed retries — only for recoverable
failure classes, only while budget remains and no cancellation was
observed. This is a retry of the model invocation itself, never of the
turn, the MCP/Domain invoke or any material operation.
"""

from __future__ import annotations

from app.application.model_invocation.errors import (
    INVALID_STRUCTURED_OUTPUT,
    PROVIDER_UNAVAILABLE,
    TIMEOUT,
)

LLM_CALL_MAX_ATTEMPTS = 3

# Recoverable classes: the same bounded request may legitimately
# succeed on a fresh invocation (inference timeout, transient adapter/
# transport failure, malformed structured output). Everything else —
# rejected, invalid request, unsupported model, policy denial,
# evaluation failure — is definitive: no retry may invent a different
# outcome or re-spend budget on a call that cannot succeed.
RECOVERABLE_CALL_ERROR_CODES = frozenset(
    {TIMEOUT, PROVIDER_UNAVAILABLE, INVALID_STRUCTURED_OUTPUT}
)


def call_retry_eligible(error_code: str, attempt: int) -> bool:
    """Whether a failed real invocation may lawfully be retried —
    bounded at ``LLM_CALL_MAX_ATTEMPTS`` real invocations total."""
    return (
        error_code in RECOVERABLE_CALL_ERROR_CODES
        and attempt < LLM_CALL_MAX_ATTEMPTS
    )
