"""Fail-closed usage-rights policy derived from ``allowed_use_scope``.

The catalog records *which operations* a source's rights evidence covers:
``collect``, ``store``, ``derive``, ``internal_display``, ``redistribute``.
Only an explicitly granted bare token counts — a qualifier such as
``internal_display_pending_lme_review`` or ``no_redistribution_*`` is not
a grant, and any pending/blocked qualifier revokes the operation even if
the bare token also appears. The license decision is institutional and
recorded in the catalog; this module only enforces the recorded state.
"""

from __future__ import annotations

OP_COLLECT = "collect"
OP_STORE = "store"
OP_DERIVE = "derive"
OP_INTERNAL_DISPLAY = "internal_display"
OP_REDISTRIBUTE = "redistribute"

KNOWN_OPERATIONS = (
    OP_COLLECT,
    OP_STORE,
    OP_DERIVE,
    OP_INTERNAL_DISPLAY,
    OP_REDISTRIBUTE,
)


def parse_scope(scope: str | None) -> frozenset[str]:
    return frozenset(
        token.strip() for token in (scope or "").split(";") if token.strip()
    )


def allows(scope: str | None, operation: str) -> bool:
    """Whether ``operation`` is granted by ``scope`` — fail-closed.

    Granted requires the bare token; a ``<op>_pending_*`` or ``no_<op>*``
    qualifier revokes it regardless.
    """
    tokens = parse_scope(scope)
    if operation not in tokens:
        return False
    return not any(
        token.startswith(f"{operation}_pending")
        or token.startswith(f"no_{operation}")
        for token in tokens
    )


def allows_all(scope: str | None, operations) -> bool:
    return all(allows(scope, operation) for operation in operations)
