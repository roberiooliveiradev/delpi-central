from uuid import uuid4

from flask import g, has_request_context, request


def resolve_audit_trace_id() -> str | None:
    if not has_request_context():
        return None

    header_trace = (
        request.headers.get("X-Trace-ID")
        or request.headers.get("X-Request-ID")
        or ""
    ).strip()

    if header_trace:
        return header_trace[:64]

    existing = getattr(g, "trace_id", None) or getattr(g, "request_id", None)

    if existing:
        return str(existing)[:64]

    generated = str(uuid4())
    g.trace_id = generated
    g.request_id = generated
    return generated
