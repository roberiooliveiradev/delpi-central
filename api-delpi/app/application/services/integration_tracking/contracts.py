"""Ports and DTOs for integration write-operation tracking.

The repository port is deliberately narrow: one atomic insert
(operation + first event), one atomic transition (operation update +
append-only event) and reads. Adapters must guarantee that the two
writes inside each method commit in a single transaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NewOperationInput:
    """Everything needed to persist a CREATED operation atomically."""

    operation_id: str
    correlation_id: str | None
    request_id: str | None
    idempotency_key: str | None
    integration: str
    resource: str
    action: str
    resource_key: str | None
    environment_key: str | None
    company_scope: str | None
    caller_app: str | None
    actor_subject: str | None
    protheus_user_id: str | None
    authorization_context: str | None
    request_payload: dict | None
    outbound_payload: dict | None
    request_hash: str | None
    outbound_hash: str | None
    payload_schema_version: int


@dataclass(frozen=True, slots=True)
class TransitionPatch:
    """Columns to update alongside a status transition."""

    status_to: str
    event_type: str
    event_data: dict | None = None
    response_payload: dict | None = None
    http_status: int | None = None
    upstream_error_code: str | None = None
    error_details: dict | None = None
    confirmation_evidence: dict | None = None
    attempt_count: int | None = None
    resource_key: str | None = None
    send_started_at: bool = False
    acknowledged_at: bool = False
    confirmed_at: bool = False


class IntegrationOperationRepository(Protocol):
    """Persistence port — implementations must be transactional."""

    def insert_operation(
        self, data: NewOperationInput, *, schema_version: int
    ) -> None:
        """Atomically insert the operation (CREATED) and its first event."""
        ...

    def apply_transition(
        self,
        operation_id: str,
        *,
        expected_version: int,
        expected_status: str,
        patch: TransitionPatch,
        correlation_id: str | None,
    ) -> None:
        """Atomically update the operation and append the transition event.

        Must raise IntegrationOperationConflictError when the stored
        version/status no longer matches (concurrent modification).
        """
        ...

    def get_operation(self, operation_id: str) -> dict | None:
        """Return the operation row as a plain dict, or None."""
        ...

    def list_events(
        self, operation_id: str, *, limit: int, offset: int
    ) -> list[dict]:
        """Return events ordered by sequence_number ascending."""
        ...
