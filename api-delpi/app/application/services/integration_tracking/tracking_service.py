"""Application service — lifecycle of an integration write operation.

Every mutating method performs exactly one transactional repository call
(operation update + append-only event). Failures propagate as
IntegrationTrackingError so callers fail closed BEFORE the upstream write
and never retry the write after a tracking failure.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.application.services.integration_tracking.contracts import (
    IntegrationOperationRepository,
    NewOperationInput,
    TransitionPatch,
)
from app.application.services.integration_tracking.payload_sanitizer import (
    build_confirmation_evidence,
    build_error_details,
    enforce_size_limit,
)
from app.domain.integrations.integration_operation import (
    ALLOWED_TRANSITIONS,
    IntegrationStatus,
    IntegrationTrackingError,
    assert_transition,
)

logger = logging.getLogger("api_delpi.integration_tracking")

SCHEMA_VERSION = 1
EVENT_CREATED = "operation_created"
EVENT_SEND_STARTED = "send_started"
EVENT_UPSTREAM_RESPONSE = "upstream_response"
EVENT_STATUS_TRANSITION = "status_transition"
EVENT_CONFIRMATION_FAILED = "confirmation_attempt_failed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IntegrationTrackingService:
    """Coordinates persistence of integration write operations."""

    def __init__(self, repository: IntegrationOperationRepository) -> None:
        self._repository = repository

    # ------------------------------------------------------------------ reads

    def get_operation(self, operation_id: str) -> dict | None:
        return self._repository.get_operation(operation_id)

    def list_events(
        self, operation_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))
        return self._repository.list_events(
            operation_id, limit=limit, offset=offset
        )

    def list_supplier_provenance(
        self,
        *,
        supplier_id: str,
        caller_app: str | None,
        actor_subject: str | None,
        field_key: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Per-field provenance for one supplier, scoped to the caller.

        ``latest_confirmed`` considers ONLY operations whose authoritative
        status is CONFIRMED — ACK/UNKNOWN/pending attempts never replace it.
        Attempts remain visible separately, ordered newest first.
        """
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))
        rows = self._repository.list_supplier_field_provenance(
            resource_key=supplier_id,
            supplier_code=supplier_id[:6],
            supplier_store=supplier_id[6:],
            caller_app=caller_app,
            actor_subject=actor_subject,
            field_key=field_key,
            limit=limit,
            offset=offset,
        )
        by_field: dict[str, list[dict]] = {}
        for row in rows:
            by_field.setdefault(str(row["field_key"]), []).append(row)

        fields = []
        for key, items in sorted(by_field.items()):
            confirmed = [
                item
                for item in items
                if item.get("operation_status") == "CONFIRMED"
            ]
            latest = confirmed[0] if confirmed else None
            pending_newer = (
                any(
                    item.get("operation_status") != "CONFIRMED"
                    for item in items[: items.index(latest)]
                )
                if latest is not None
                else bool(items)
            )
            fields.append(
                {
                    "field_key": key,
                    "latest_confirmed": self._project_provenance(latest)
                    if latest
                    else None,
                    "has_unconfirmed_newer_attempts": pending_newer,
                    "attempt_count": len(items),
                }
            )

        return {
            "supplier_id": supplier_id,
            "fields": fields,
            "attempts": [self._project_provenance(row) for row in rows],
            "page": {"limit": limit, "offset": offset},
        }

    @staticmethod
    def _project_provenance(row: dict | None) -> dict | None:
        if row is None:
            return None
        return {
            "provenance_id": row.get("provenance_id"),
            "operation_id": row.get("operation_id"),
            "field_key": row.get("field_key"),
            "source_type": row.get("source_type"),
            "change_mode": row.get("change_mode"),
            "source_id": row.get("source_id"),
            "source_reference": row.get("source_reference"),
            "source_retrieved_at": row.get("source_retrieved_at"),
            "reason_code": row.get("reason_code"),
            "review_id": row.get("review_id"),
            "decision_id": row.get("decision_id"),
            "initiating_client_id": row.get("initiating_client_id"),
            "operation_status": row.get("operation_status"),
            "operation_action": row.get("operation_action"),
            "recorded_at": row.get("created_at"),
            "confirmed_at": row.get("operation_confirmed_at"),
        }

    # --------------------------------------------------------------- creation

    def begin_operation(
        self,
        *,
        integration: str,
        resource: str,
        action: str,
        resource_key: str | None,
        environment_key: str | None,
        company_scope: str | None,
        caller_app: str | None,
        actor_subject: str | None,
        protheus_user_id: str | None,
        authorization_context: str | None,
        request_payload: dict | None,
        outbound_payload: dict | None,
        request_hash: str | None,
        outbound_hash: str | None,
        correlation_id: str | None,
        request_id: str | None,
        idempotency_key: str | None = None,
        field_provenance: list[dict] | None = None,
    ) -> str:
        """Persist the CREATED operation atomically. Fail closed on error."""
        operation_id = str(uuid.uuid4())
        data = NewOperationInput(
            operation_id=operation_id,
            correlation_id=correlation_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
            integration=integration,
            resource=resource,
            action=action,
            resource_key=resource_key,
            environment_key=environment_key,
            company_scope=company_scope,
            caller_app=caller_app,
            actor_subject=actor_subject,
            protheus_user_id=protheus_user_id,
            authorization_context=authorization_context,
            request_payload=enforce_size_limit(request_payload),
            outbound_payload=enforce_size_limit(outbound_payload),
            request_hash=request_hash,
            outbound_hash=outbound_hash,
            payload_schema_version=1,
            field_provenance=tuple(field_provenance or ()),
        )
        self._repository.insert_operation(data, schema_version=SCHEMA_VERSION)
        logger.info(
            "integration_operation_created operation_id=%s integration=%s "
            "resource=%s action=%s caller_app=%s",
            operation_id,
            integration,
            resource,
            action,
            caller_app or "-",
        )
        return operation_id

    # ------------------------------------------------------------ transitions

    def _load_or_raise(self, operation_id: str) -> dict:
        row = self._repository.get_operation(operation_id)
        if row is None:
            raise IntegrationTrackingError(
                f"Integration operation {operation_id} not found.",
                code="INTEGRATION_OPERATION_NOT_FOUND",
            )
        return row

    def _transition(
        self,
        operation_id: str,
        to_status: IntegrationStatus,
        *,
        patch: TransitionPatch,
        correlation_id: str | None = None,
    ) -> None:
        row = self._load_or_raise(operation_id)
        status_from = IntegrationStatus(str(row["status"]))
        assert_transition(status_from, to_status)
        self._repository.apply_transition(
            operation_id,
            expected_version=int(row["version"]),
            expected_status=status_from.value,
            patch=patch,
            correlation_id=correlation_id or row.get("correlation_id"),
        )
        logger.info(
            "integration_operation_transition operation_id=%s %s->%s",
            operation_id,
            status_from.value,
            to_status.value,
        )

    def mark_sending(self, operation_id: str) -> None:
        """CREATED -> SENDING. Must commit before the upstream call."""
        self._transition(
            operation_id,
            IntegrationStatus.SENDING,
            patch=TransitionPatch(
                status_to=IntegrationStatus.SENDING.value,
                event_type=EVENT_SEND_STARTED,
                send_started_at=True,
                attempt_count=1,
            ),
        )

    def record_acknowledged(
        self,
        operation_id: str,
        *,
        http_status: int | None,
        response_payload: dict | None,
        resource_key: str | None = None,
    ) -> None:
        """SENDING -> ACKNOWLEDGED (upstream 2xx, persistence NOT proven)."""
        self._transition(
            operation_id,
            IntegrationStatus.ACKNOWLEDGED,
            patch=TransitionPatch(
                status_to=IntegrationStatus.ACKNOWLEDGED.value,
                event_type=EVENT_UPSTREAM_RESPONSE,
                response_payload=enforce_size_limit(response_payload),
                http_status=http_status,
                acknowledged_at=True,
                resource_key=resource_key,
            ),
        )

    def record_rejected(
        self,
        operation_id: str,
        *,
        http_status: int | None,
        code: str,
        message: str,
    ) -> None:
        """SENDING -> REJECTED — deterministic failure, proven no-write."""
        self._transition(
            operation_id,
            IntegrationStatus.REJECTED,
            patch=TransitionPatch(
                status_to=IntegrationStatus.REJECTED.value,
                event_type=EVENT_UPSTREAM_RESPONSE,
                http_status=http_status,
                upstream_error_code=code,
                error_details=build_error_details(
                    category="UPSTREAM_REJECTION",
                    code=code,
                    message=message,
                    retry_safe=False,
                    http_status=http_status,
                ),
                acknowledged_at=True,
            ),
        )

    def mark_outcome_unknown(
        self,
        operation_id: str,
        *,
        http_status: int | None,
        code: str,
        message: str,
    ) -> None:
        """SENDING -> UNKNOWN — timeout/5xx after a possible send.

        Never auto-retry: the write may have been applied upstream.
        """
        self._transition(
            operation_id,
            IntegrationStatus.UNKNOWN,
            patch=TransitionPatch(
                status_to=IntegrationStatus.UNKNOWN.value,
                event_type=EVENT_UPSTREAM_RESPONSE,
                http_status=http_status,
                upstream_error_code=code,
                error_details=build_error_details(
                    category="INDETERMINATE_OUTCOME",
                    code=code,
                    message=message,
                    retry_safe=False,
                    http_status=http_status,
                ),
            ),
        )

    def mark_failed_pre_send(
        self, operation_id: str, *, code: str, message: str
    ) -> None:
        """CREATED -> FAILED_PRE_SEND — failure proven before transmission."""
        self._transition(
            operation_id,
            IntegrationStatus.FAILED_PRE_SEND,
            patch=TransitionPatch(
                status_to=IntegrationStatus.FAILED_PRE_SEND.value,
                event_type=EVENT_STATUS_TRANSITION,
                upstream_error_code=code,
                error_details=build_error_details(
                    category="PRE_SEND_FAILURE",
                    code=code,
                    message=message,
                    retry_safe=True,
                ),
            ),
        )

    def record_confirmation_failure(
        self, operation_id: str, *, code: str, message: str
    ) -> None:
        """Append a non-transition event — operation stays ACKNOWLEDGED."""
        row = self._load_or_raise(operation_id)
        self._repository.apply_transition(
            operation_id,
            expected_version=int(row["version"]),
            expected_status=str(row["status"]),
            patch=TransitionPatch(
                status_to=str(row["status"]),
                event_type=EVENT_CONFIRMATION_FAILED,
                event_data=build_error_details(
                    category="CONFIRMATION_FAILURE",
                    code=code,
                    message=message,
                    retry_safe=True,
                ),
            ),
            correlation_id=row.get("correlation_id"),
        )

    def confirm(
        self,
        operation_id: str,
        *,
        evidence: dict | None,
        resource_key: str | None = None,
        checked_fields: list[str] | None = None,
        result: str = "MATCH",
        method: str = "READ_AFTER_WRITE",
    ) -> None:
        """* -> CONFIRMED when the domain allows it, with stored evidence."""
        row = self._load_or_raise(operation_id)
        full_evidence = evidence or build_confirmation_evidence(
            method=method,
            resource_key=resource_key or row.get("resource_key"),
            environment_key=row.get("environment_key"),
            checked_fields=checked_fields or [],
            result=result,
        )
        self._transition(
            operation_id,
            IntegrationStatus.CONFIRMED,
            patch=TransitionPatch(
                status_to=IntegrationStatus.CONFIRMED.value,
                event_type=EVENT_STATUS_TRANSITION,
                confirmation_evidence=enforce_size_limit(full_evidence),
                confirmed_at=True,
                event_data={
                    "method": method,
                    "result": result,
                    "checked_at": _utcnow().isoformat(),
                },
            ),
        )

    def require_reconciliation(
        self, operation_id: str, *, code: str, message: str
    ) -> None:
        """* -> RECONCILIATION_REQUIRED — human/system investigation needed."""
        self._transition(
            operation_id,
            IntegrationStatus.RECONCILIATION_REQUIRED,
            patch=TransitionPatch(
                status_to=IntegrationStatus.RECONCILIATION_REQUIRED.value,
                event_type=EVENT_STATUS_TRANSITION,
                upstream_error_code=code,
                error_details=build_error_details(
                    category="RECONCILIATION",
                    code=code,
                    message=message,
                    retry_safe=False,
                ),
            ),
        )

    # ---------------------------------------------------------- authorization

    @staticmethod
    def assert_can_view(
        operation: dict,
        *,
        caller_app: str | None,
        actor_subject: str | None,
    ) -> None:
        """Bind a read to its owner: same caller app AND same actor subject.

        A consumer app may never read another app's operation, and a user may
        never read another user's operation, just by knowing the UUID.
        """
        op_caller = operation.get("caller_app")
        op_actor = operation.get("actor_subject")
        if op_caller != (caller_app or None):
            raise IntegrationTrackingError(
                "Operation belongs to a different caller application.",
                code="INTEGRATION_OPERATION_FORBIDDEN",
            )
        if op_actor != (actor_subject or None):
            raise IntegrationTrackingError(
                "Operation belongs to a different actor.",
                code="INTEGRATION_OPERATION_FORBIDDEN",
            )


def describe_status_machine() -> dict[str, Any]:
    """Documentation aid — statuses and allowed transitions."""
    return {
        status.value: sorted(target.value for target in targets)
        for status, targets in ALLOWED_TRANSITIONS.items()
    }
