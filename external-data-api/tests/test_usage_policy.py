"""Usage-rights policy — fail-closed semantics (PROC-0076 R1.2).

Only explicitly granted bare scope tokens authorize an operation;
``*_pending_*`` / ``no_*`` qualifiers never do.
"""

from __future__ import annotations

from app.domain import usage_policy
from app.domain.usage_policy import allows, allows_all, parse_scope

FULL = "collect;store;derive;internal_display"
LME_PENDING = (
    "collect;store;derive;internal_display_pending_lme_review;"
    "no_redistribution_pending_lme_review"
)


def test_parse_scope_splits_semicolons():
    assert parse_scope("a; b ;;") == frozenset({"a", "b"})
    assert parse_scope(None) == frozenset()
    assert parse_scope("") == frozenset()


def test_granted_operations_allowed():
    for op in ("collect", "store", "derive", "internal_display"):
        assert allows(FULL, op) is True
    assert allows(FULL, "redistribute") is False


def test_pending_qualifier_is_not_a_grant():
    assert allows(LME_PENDING, "internal_display") is False
    assert allows(LME_PENDING, "redistribute") is False
    # Unrelated grants still hold.
    for op in ("collect", "store", "derive"):
        assert allows(LME_PENDING, op) is True


def test_pending_revokes_even_when_bare_token_present():
    scope = "internal_display;internal_display_pending_x"
    assert allows(scope, "internal_display") is False


def test_unknown_and_empty_scope_deny_everything():
    for op in usage_policy.KNOWN_OPERATIONS:
        assert allows(None, op) is False
        assert allows("", op) is False
        assert allows("something;else", op) is False


def test_allows_all_requires_every_operation():
    assert allows_all(FULL, ("collect", "store")) is True
    assert allows_all(LME_PENDING, ("collect", "internal_display")) is False
    assert allows_all("collect", ("collect", "store")) is False
