"""Integration write-operation tracking — domain model.

Persisted execution record for writes that api-delpi forwards to upstream
providers (currently TOTVS Protheus REST). Pure domain: no framework, SQL,
HTTP or ORM dependencies.

Semantics:
- ``SENDING`` records that transmission started or may have started; it is
  never proof of delivery.
- ``ACKNOWLEDGED`` means an upstream 2xx response arrived; it is never proof
  of persistence.
- ``CONFIRMED`` requires read-after-write (or equivalent) evidence.
- A 5xx/timeout after a possible send is ``UNKNOWN``, never ``REJECTED``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IntegrationStatus(str, Enum):
    CREATED = "CREATED"
    SENDING = "SENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    FAILED_PRE_SEND = "FAILED_PRE_SEND"
    UNKNOWN = "UNKNOWN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


# Allowed status transitions. Anything outside this map is a domain violation.
ALLOWED_TRANSITIONS: dict[IntegrationStatus, frozenset[IntegrationStatus]] = {
    IntegrationStatus.CREATED: frozenset(
        {IntegrationStatus.SENDING, IntegrationStatus.FAILED_PRE_SEND}
    ),
    IntegrationStatus.SENDING: frozenset(
        {
            IntegrationStatus.ACKNOWLEDGED,
            IntegrationStatus.REJECTED,
            IntegrationStatus.UNKNOWN,
        }
    ),
    IntegrationStatus.ACKNOWLEDGED: frozenset(
        {IntegrationStatus.CONFIRMED, IntegrationStatus.RECONCILIATION_REQUIRED}
    ),
    IntegrationStatus.UNKNOWN: frozenset(
        {IntegrationStatus.CONFIRMED, IntegrationStatus.RECONCILIATION_REQUIRED}
    ),
    IntegrationStatus.RECONCILIATION_REQUIRED: frozenset(
        {IntegrationStatus.CONFIRMED}
    ),
    IntegrationStatus.CONFIRMED: frozenset(),
    IntegrationStatus.REJECTED: frozenset(),
    IntegrationStatus.FAILED_PRE_SEND: frozenset(),
}

# Terminal states — no further transition may leave them.
TERMINAL_STATUSES: frozenset[IntegrationStatus] = frozenset(
    {
        IntegrationStatus.CONFIRMED,
        IntegrationStatus.REJECTED,
        IntegrationStatus.FAILED_PRE_SEND,
    }
)

# Post-send indeterminate outcomes — never auto-retry these operations.
INDETERMINATE_STATUSES: frozenset[IntegrationStatus] = frozenset(
    {IntegrationStatus.SENDING, IntegrationStatus.UNKNOWN}
)

VALID_ACTIONS = frozenset({"create", "update"})


class IntegrationTrackingError(RuntimeError):
    """Domain/persistence error of the integration tracking subsystem."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "INTEGRATION_TRACKING_ERROR",
        recoverable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.recoverable = recoverable


class InvalidTransitionError(IntegrationTrackingError):
    """A status transition outside ALLOWED_TRANSITIONS was attempted."""

    def __init__(self, status_from: str, status_to: str) -> None:
        super().__init__(
            f"Invalid status transition: {status_from} -> {status_to}.",
            code="INTEGRATION_OPERATION_INVALID_TRANSITION",
        )
        self.status_from = status_from
        self.status_to = status_to


class IntegrationOperationConflictError(IntegrationTrackingError):
    """Concurrent update or stale version on the same operation."""

    def __init__(self, operation_id: str) -> None:
        super().__init__(
            f"Integration operation {operation_id} changed concurrently.",
            code="INTEGRATION_OPERATION_CONFLICT",
        )


def assert_transition(
    status_from: IntegrationStatus, status_to: IntegrationStatus
) -> None:
    """Domain gate — raises InvalidTransitionError for illegal moves."""
    allowed = ALLOWED_TRANSITIONS.get(status_from, frozenset())
    if status_to not in allowed:
        raise InvalidTransitionError(status_from.value, status_to.value)


@dataclass(frozen=True, slots=True)
class IntegrationOperation:
    """Current snapshot of one logical write operation."""

    operation_id: str
    schema_version: int
    integration: str
    resource: str
    action: str
    status: IntegrationStatus
    version: int
    correlation_id: str | None
    request_id: str | None
    idempotency_key: str | None
    resource_key: str | None
    environment_key: str | None
    company_scope: str | None
    caller_app: str | None
    actor_subject: str | None
    protheus_user_id: str | None
    authorization_context: str | None
    request_payload: dict | None
    outbound_payload: dict | None
    response_payload: dict | None
    request_hash: str | None
    outbound_hash: str | None
    payload_schema_version: int
    http_status: int | None
    upstream_error_code: str | None
    error_details: dict | None
    confirmation_evidence: dict | None
    attempt_count: int
    created_at: object
    send_started_at: object | None
    acknowledged_at: object | None
    confirmed_at: object | None
    updated_at: object


@dataclass(frozen=True, slots=True)
class IntegrationOperationEvent:
    """Append-only transition/annotation record of an operation."""

    event_id: str
    operation_id: str
    sequence_number: int
    event_type: str
    status_from: str | None
    status_to: str | None
    event_data: dict | None
    occurred_at: object
    correlation_id: str | None
