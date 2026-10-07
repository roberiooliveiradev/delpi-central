"""Purchase request (SC1) TOTVS semantics — canonical mappings."""

from __future__ import annotations


def map_purchase_request_approval_status(raw: str | None) -> str:
    """Map ``SC1.C1_APROV`` to the semantic approval status.

    ``L`` → approved, ``R`` → rejected, ``B`` → blocked, anything else
    (including blank) → unknown.
    """
    value = (raw or "").strip().upper()
    if value == "L":
        return "approved"
    if value == "R":
        return "rejected"
    if value == "B":
        return "blocked"
    return "unknown"
