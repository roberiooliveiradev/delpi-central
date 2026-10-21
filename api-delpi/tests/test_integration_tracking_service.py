"""Tracking service tests — lifecycle, transitions, conflicts, reads."""

from __future__ import annotations

import pytest

from app.application.services.integration_tracking.contracts import (
    NewOperationInput,
    TransitionPatch,
)
from app.application.services.integration_tracking.tracking_service import (
    IntegrationTrackingService,
)
from app.domain.integrations.integration_operation import (
    IntegrationOperationConflictError,
    IntegrationTrackingError,
    InvalidTransitionError,
)


class InMemoryIntegrationOperationRepository:
    """Fake adapter honoring the repository contract."""

    def __init__(self) -> None:
        self.operations: dict[str, dict] = {}
        self.events: dict[str, list[dict]] = {}
        self.fail_next_insert = False
        self.fail_next_transition = False
        self.conflict_next_transition = False

    def insert_operation(
        self, data: NewOperationInput, *, schema_version: int
    ) -> None:
        if self.fail_next_insert:
            self.fail_next_insert = False
            raise IntegrationTrackingError("db down")
        self.operations[data.operation_id] = {
            "operation_id": data.operation_id,
            "status": "CREATED",
            "version": 0,
            "attempt_count": 0,
            "correlation_id": data.correlation_id,
            "caller_app": data.caller_app,
            "actor_subject": data.actor_subject,
            "resource_key": data.resource_key,
            "environment_key": data.environment_key,
            "protheus_user_id": data.protheus_user_id,
            "request_payload": data.request_payload,
            "outbound_payload": data.outbound_payload,
            "request_hash": data.request_hash,
            "outbound_hash": data.outbound_hash,
        }
        self.events[data.operation_id] = [
            {"sequence_number": 1, "event_type": "operation_created"}
        ]

    def apply_transition(
        self,
        operation_id: str,
        *,
        expected_version: int,
        expected_status: str,
        patch: TransitionPatch,
        correlation_id: str | None,
    ) -> None:
        if self.fail_next_transition:
            self.fail_next_transition = False
            raise IntegrationTrackingError("db down")
        if self.conflict_next_transition:
            self.conflict_next_transition = False
            raise IntegrationOperationConflictError(operation_id)
        row = self.operations[operation_id]
        if row["version"] != expected_version or row["status"] != expected_status:
            raise IntegrationOperationConflictError(operation_id)
        row["status"] = patch.status_to
        row["version"] += 1
        if patch.http_status is not None:
            row["http_status"] = patch.http_status
        if patch.error_details is not None:
            row["error_details"] = patch.error_details
        if patch.confirmation_evidence is not None:
            row["confirmation_evidence"] = patch.confirmation_evidence
        if patch.resource_key is not None:
            row["resource_key"] = patch.resource_key
        if patch.attempt_count is not None:
            row["attempt_count"] = patch.attempt_count
        seq = len(self.events[operation_id]) + 1
        self.events[operation_id].append(
            {
                "sequence_number": seq,
                "event_type": patch.event_type,
                "status_from": expected_status,
                "status_to": patch.status_to,
            }
        )

    def get_operation(self, operation_id: str) -> dict | None:
        return self.operations.get(operation_id)

    def list_events(
        self, operation_id: str, *, limit: int, offset: int
    ) -> list[dict]:
        return self.events.get(operation_id, [])[offset : offset + limit]


def _service_and_repo():
    repo = InMemoryIntegrationOperationRepository()
    return IntegrationTrackingService(repository=repo), repo


def _begin(service: IntegrationTrackingService) -> str:
    return service.begin_operation(
        integration="protheus",
        resource="supplier",
        action="update",
        resource_key="00387801",
        environment_key="ambiente:1@host:8701",
        company_scope=None,
        caller_app="supplies-api",
        actor_subject="user-1",
        protheus_user_id="000311",
        authorization_context=None,
        request_payload={"schema_version": 1, "fields": {}},
        outbound_payload={"schema_version": 1, "body": {}},
        request_hash="h" * 64,
        outbound_hash="o" * 64,
        correlation_id="corr-1",
        request_id="req-1",
    )


def test_begin_operation_persists_created_with_event() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    row = repo.get_operation(op_id)
    assert row["status"] == "CREATED"
    assert row["caller_app"] == "supplies-api"
    assert row["actor_subject"] == "user-1"
    assert row["protheus_user_id"] == "000311"
    events = repo.list_events(op_id, limit=10, offset=0)
    assert events[0]["event_type"] == "operation_created"


def test_begin_failure_raises_and_persists_nothing() -> None:
    service, repo = _service_and_repo()
    repo.fail_next_insert = True
    with pytest.raises(IntegrationTrackingError):
        _begin(service)
    assert repo.operations == {}


def test_full_lifecycle_acknowledged_then_confirmed() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    service.mark_sending(op_id)
    service.record_acknowledged(
        op_id, http_status=200, response_payload={"message": "ok"}
    )
    service.confirm(
        op_id, evidence={"result": "MATCH"}, checked_fields=["supplier_name"]
    )
    row = repo.get_operation(op_id)
    assert row["status"] == "CONFIRMED"
    assert row["confirmation_evidence"]["result"] == "MATCH"
    event_types = [e["event_type"] for e in repo.list_events(op_id, limit=10, offset=0)]
    assert event_types == [
        "operation_created",
        "send_started",
        "upstream_response",
        "status_transition",
    ]


def test_unknown_is_indeterminate_and_never_rejected() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    service.mark_sending(op_id)
    service.mark_outcome_unknown(
        op_id, http_status=None, code="PROTHEUS_TIMEOUT", message="t/o"
    )
    assert repo.get_operation(op_id)["status"] == "UNKNOWN"
    # UNKNOWN -> REJECTED is a domain violation (no proof of no-write).
    from app.domain.integrations.integration_operation import (
        IntegrationStatus,
        assert_transition,
    )

    with pytest.raises(InvalidTransitionError):
        assert_transition(IntegrationStatus.UNKNOWN, IntegrationStatus.REJECTED)


def test_unknown_can_confirm_with_evidence() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    service.mark_sending(op_id)
    service.mark_outcome_unknown(
        op_id, http_status=500, code="PROTHEUS_UPSTREAM_ERROR", message="500"
    )
    service.require_reconciliation(
        op_id, code="MANUAL_CHECK", message="verificar SA2"
    )
    service.confirm(op_id, evidence={"result": "MATCH"}, checked_fields=[])
    assert repo.get_operation(op_id)["status"] == "CONFIRMED"


def test_rejected_is_terminal() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    service.mark_sending(op_id)
    service.record_rejected(
        op_id, http_status=400, code="PROTHEUS_SUPPLIER_WRITE_MATA020_FAILED",
        message="rejeitado",
    )
    assert repo.get_operation(op_id)["status"] == "REJECTED"
    with pytest.raises(InvalidTransitionError):
        service.mark_sending(op_id)


def test_mark_sending_requires_created() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    service.mark_sending(op_id)
    with pytest.raises(InvalidTransitionError):
        service.mark_sending(op_id)


def test_failed_pre_send_terminal() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    service.mark_failed_pre_send(
        op_id, code="TOKEN_RESOLVE_FAILED", message="oauth fail"
    )
    assert repo.get_operation(op_id)["status"] == "FAILED_PRE_SEND"


def test_conflict_on_stale_version() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    repo.conflict_next_transition = True  # simulated concurrent mutation
    with pytest.raises(IntegrationOperationConflictError):
        service.mark_sending(op_id)
    # Operation status unchanged — the transition rolled back atomically.
    assert repo.get_operation(op_id)["status"] == "CREATED"
    assert len(repo.list_events(op_id, limit=10, offset=0)) == 1


def test_confirmation_failure_appends_event_without_transition() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    service.mark_sending(op_id)
    service.record_acknowledged(
        op_id, http_status=200, response_payload={"message": "ok"}
    )
    service.record_confirmation_failure(
        op_id, code="GET_FAILED", message="read-back 502"
    )
    row = repo.get_operation(op_id)
    assert row["status"] == "ACKNOWLEDGED"
    last = repo.list_events(op_id, limit=10, offset=0)[-1]
    assert last["event_type"] == "confirmation_attempt_failed"


def test_assert_can_view_binds_caller_and_actor() -> None:
    service, repo = _service_and_repo()
    op_id = _begin(service)
    op = repo.get_operation(op_id)
    service.assert_can_view(
        op, caller_app="supplies-api", actor_subject="user-1"
    )
    with pytest.raises(IntegrationTrackingError):
        service.assert_can_view(
            op, caller_app="other-app", actor_subject="user-1"
        )
    with pytest.raises(IntegrationTrackingError):
        service.assert_can_view(
            op, caller_app="supplies-api", actor_subject="user-2"
        )


def test_get_unknown_operation_raises_not_found() -> None:
    service, _ = _service_and_repo()
    with pytest.raises(IntegrationTrackingError) as exc_info:
        service.mark_sending("00000000-0000-0000-0000-000000000000")
    assert exc_info.value.code == "INTEGRATION_OPERATION_NOT_FOUND"
