"""Request-scoped subject bearer accessor — C3-MCP-INTEROP-01R1A.

The auth middleware stores the already-authenticated Portal bearer on
``flask.g`` for the duration of one request so Infrastructure can
perform user-delegated credential exchange. The bearer is never
persisted, logged, serialized, placed in ``PlatformAccessContext``, or
propagated to model/MFE surfaces.

DELIA-C3-NDJSON-SUBJECT-BEARER-CONTEXT-HOTFIX-01: the opt-in NDJSON
transport executes the use case on a bounded worker thread, where no
Flask request context exists. For that transport only, the HTTP layer
binds the already-authenticated bearer to the worker's execution
context via ``bind_subject_bearer``/``unbind_subject_bearer``
(set/reset in try/finally). The ContextVar is context-local — a token
bound on one thread is invisible to any other. The legacy ``flask.g``
path is preserved unchanged and remains the source for the request
thread itself.
"""

from __future__ import annotations

import contextvars

_BOUND_BEARER: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "delia_subject_bearer_binding", default=None
)


def bind_subject_bearer(bearer: str) -> contextvars.Token:
    """Bind an already-authenticated bearer to THIS execution context.

    Transport-only seam: called by the NDJSON worker with the token
    captured on the request thread. Returns the ContextVar token so the
    binder can restore the previous value — callers MUST unbind in a
    finally block so the bearer never outlives the execution.
    """
    return _BOUND_BEARER.set(bearer)


def unbind_subject_bearer(binding: contextvars.Token) -> None:
    """Restore the previous binding — always called from the context
    that created it (try/finally at the transport boundary)."""
    _BOUND_BEARER.reset(binding)


def current_subject_bearer() -> str | None:
    """Return the current request's subject bearer, or None."""
    bound = _BOUND_BEARER.get()
    if bound:
        return bound
    from flask import g, has_request_context

    if not has_request_context():
        return None
    value = getattr(g, "subject_bearer", None)
    if isinstance(value, str) and value.strip():
        return value
    return None
