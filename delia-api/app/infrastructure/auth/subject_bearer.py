"""Request-scoped subject bearer accessor — C3-MCP-INTEROP-01R1A.

The auth middleware stores the already-authenticated Portal bearer on
``flask.g`` for the duration of one request so Infrastructure can
perform user-delegated credential exchange. The bearer is never
persisted, logged, serialized, placed in ``PlatformAccessContext``, or
propagated to model/MFE surfaces.
"""

from __future__ import annotations


def current_subject_bearer() -> str | None:
    """Return the current request's subject bearer, or None."""
    from flask import g, has_request_context

    if not has_request_context():
        return None
    value = getattr(g, "subject_bearer", None)
    if isinstance(value, str) and value.strip():
        return value
    return None
