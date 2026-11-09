"""Governed lifecycle for MCP provider registrations (Core-owned).

registered != approved != enabled != authenticated != authorized.
No secrets or tools/list catalogs belong here.
"""

from __future__ import annotations

from typing import Final

STATUS_DISCOVERED: Final = "DISCOVERED"
STATUS_REVIEWED: Final = "REVIEWED"
STATUS_APPROVED: Final = "APPROVED"
STATUS_REJECTED: Final = "REJECTED"
STATUS_ACTIVE: Final = "ACTIVE"
STATUS_DEGRADED: Final = "DEGRADED"
STATUS_DISABLED: Final = "DISABLED"
STATUS_REVOKED: Final = "REVOKED"
STATUS_DEPRECATED: Final = "DEPRECATED"

ALL_STATUSES: Final = frozenset(
    {
        STATUS_DISCOVERED,
        STATUS_REVIEWED,
        STATUS_APPROVED,
        STATUS_REJECTED,
        STATUS_ACTIVE,
        STATUS_DEGRADED,
        STATUS_DISABLED,
        STATUS_REVOKED,
        STATUS_DEPRECATED,
    }
)

AUTH_STRATEGY_KEYCLOAK_DELEGATED: Final = "KEYCLOAK_DELEGATED"
AUTH_STRATEGY_EXTERNAL_OAUTH: Final = "EXTERNAL_OAUTH"
AUTH_STRATEGY_NONE: Final = "NONE"

ALLOWED_AUTH_STRATEGIES: Final = frozenset(
    {
        AUTH_STRATEGY_KEYCLOAK_DELEGATED,
        AUTH_STRATEGY_EXTERNAL_OAUTH,
        AUTH_STRATEGY_NONE,
    }
)

PROTOCOL_MCP: Final = "MCP"

# Eligible for DÉLIA consumption: approved/active/degraded AND enabled.
ELIGIBLE_STATUSES: Final = frozenset(
    {STATUS_APPROVED, STATUS_ACTIVE, STATUS_DEGRADED}
)

_TRANSITIONS: Final[dict[str, frozenset[str]]] = {
    STATUS_DISCOVERED: frozenset(
        {STATUS_REVIEWED, STATUS_APPROVED, STATUS_REJECTED, STATUS_REVOKED}
    ),
    STATUS_REVIEWED: frozenset(
        {STATUS_APPROVED, STATUS_REJECTED, STATUS_REVOKED, STATUS_DEPRECATED}
    ),
    STATUS_APPROVED: frozenset(
        {
            STATUS_ACTIVE,
            STATUS_DISABLED,
            STATUS_REVOKED,
            STATUS_DEPRECATED,
            STATUS_REJECTED,
        }
    ),
    STATUS_ACTIVE: frozenset(
        {
            STATUS_DEGRADED,
            STATUS_DISABLED,
            STATUS_REVOKED,
            STATUS_DEPRECATED,
            STATUS_APPROVED,
        }
    ),
    STATUS_DEGRADED: frozenset(
        {STATUS_ACTIVE, STATUS_DISABLED, STATUS_REVOKED, STATUS_DEPRECATED}
    ),
    STATUS_DISABLED: frozenset(
        {STATUS_ACTIVE, STATUS_APPROVED, STATUS_REVOKED, STATUS_DEPRECATED}
    ),
    STATUS_REJECTED: frozenset({STATUS_DISCOVERED, STATUS_REVOKED, STATUS_DEPRECATED}),
    STATUS_REVOKED: frozenset(),
    STATUS_DEPRECATED: frozenset(),
}


class McpProviderLifecycleError(ValueError):
    """Illegal lifecycle transition or invalid field."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def assert_status(status: str) -> str:
    normalized = str(status or "").strip().upper()
    if normalized not in ALL_STATUSES:
        raise McpProviderLifecycleError(
            "mcp_provider.invalid_status",
            f"Unknown approval_status: {status!r}",
        )
    return normalized


def assert_auth_strategy(strategy: str) -> str:
    normalized = str(strategy or "").strip().upper()
    if normalized not in ALLOWED_AUTH_STRATEGIES:
        raise McpProviderLifecycleError(
            "mcp_provider.invalid_auth_strategy",
            f"Unknown auth_strategy_ref: {strategy!r}",
        )
    return normalized


def can_transition(current: str, target: str) -> bool:
    cur = assert_status(current)
    tgt = assert_status(target)
    if cur == tgt:
        return True
    return tgt in _TRANSITIONS.get(cur, frozenset())


def transition(current: str, target: str) -> str:
    cur = assert_status(current)
    tgt = assert_status(target)
    if cur == tgt:
        return cur
    if tgt not in _TRANSITIONS.get(cur, frozenset()):
        raise McpProviderLifecycleError(
            "mcp_provider.illegal_transition",
            f"Cannot transition from {cur} to {tgt}",
        )
    return tgt


def is_eligible(*, approval_status: str, enabled: bool) -> bool:
    status = assert_status(approval_status)
    return bool(enabled) and status in ELIGIBLE_STATUSES


def after_approve(current: str) -> tuple[str, bool]:
    """Approve candidate → APPROVED, enabled remains false until enable."""
    return transition(current, STATUS_APPROVED), False


def after_reject(current: str) -> tuple[str, bool]:
    return transition(current, STATUS_REJECTED), False


def after_enable(current: str) -> tuple[str, bool]:
    status = assert_status(current)
    if status in {STATUS_REVOKED, STATUS_DEPRECATED, STATUS_REJECTED, STATUS_DISCOVERED, STATUS_REVIEWED}:
        raise McpProviderLifecycleError(
            "mcp_provider.enable_not_allowed",
            f"Cannot enable provider in status {status}",
        )
    if status == STATUS_APPROVED or status == STATUS_DISABLED or status == STATUS_DEGRADED:
        return transition(status, STATUS_ACTIVE), True
    if status == STATUS_ACTIVE:
        return STATUS_ACTIVE, True
    raise McpProviderLifecycleError(
        "mcp_provider.enable_not_allowed",
        f"Cannot enable provider in status {status}",
    )


def after_disable(current: str) -> tuple[str, bool]:
    status = assert_status(current)
    if status in {STATUS_REVOKED, STATUS_DEPRECATED}:
        raise McpProviderLifecycleError(
            "mcp_provider.disable_not_allowed",
            f"Cannot disable provider in status {status}",
        )
    return transition(status, STATUS_DISABLED), False


def after_revoke(current: str) -> tuple[str, bool]:
    status = assert_status(current)
    if status in {STATUS_REVOKED, STATUS_DEPRECATED}:
        return status, False
    return transition(status, STATUS_REVOKED), False
