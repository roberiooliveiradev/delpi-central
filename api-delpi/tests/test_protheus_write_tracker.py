"""Write tracker + use case integration — fail-closed, outcomes, no retry."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.application.services.integration_tracking.tracking_service import (
    IntegrationTrackingService,
)
from app.application.services.integrations.protheus_write_tracker import (
    ProtheusWriteTracker,
    compare_sent_fields,
    extract_supplier_fields,
)
from app.application.use_cases.integrations.update_protheus_rest_supplier_use_case import (
    UpdateProtheusRestSupplierUseCase,
)
from app.domain.integrations.integration_operation import (
    IntegrationTrackingError,
)
from app.domain.integrations.protheus_rest import (
    ProtheusRestConfig,
    ProtheusRestError,
)

ACTOR = UUID("401b25fa-ccd1-4800-8a12-a767909956b4")
_CONFIG = ProtheusRestConfig(
    username="u",
    password="p",
    base_url="https://protheus.example/rest",
    auth_path="/api/oauth2/v1/token",
    suppliers_path="/delpi/api/v1/suppliers",
)


def _mapped(usr: str = "000161") -> dict:
    return {
        "mapping_status": "mapped",
        "verified": True,
        "protheus_user_id": usr,
    }


def _tracker_kwargs(**overrides):
    kwargs = dict(
        action="update",
        method="PUT",
        resource_key="00387801",
        environment_key="ambiente:1@host:8701",
        caller_app="supplies-api",
        actor_user_id=ACTOR,
        codusr="000161",
        request_fields={"supplier_name": "ACME"},
        outbound_body={"codusr": "000161", "fornecedor": {}},
        correlation_id="corr",
        request_id="req",
    )
    kwargs.update(overrides)
    return kwargs


# --------------------------------------------------------------- begin flow


def test_begin_fail_closed_when_insert_fails() -> None:
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.begin_operation.side_effect = IntegrationTrackingError("db")
    wt = ProtheusWriteTracker(tracker)
    with pytest.raises(ProtheusRestError) as exc_info:
        wt.begin(**_tracker_kwargs())
    assert exc_info.value.code == "PROTHEUS_TRACKING_UNAVAILABLE"
    assert exc_info.value.status_code == 503


def test_begin_fail_closed_when_mark_sending_fails() -> None:
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.begin_operation.return_value = "op-1"
    tracker.mark_sending.side_effect = IntegrationTrackingError("db")
    wt = ProtheusWriteTracker(tracker)
    with pytest.raises(ProtheusRestError) as exc_info:
        wt.begin(**_tracker_kwargs())
    assert exc_info.value.code == "PROTHEUS_TRACKING_UNAVAILABLE"


def test_begin_without_tracker_denies_send() -> None:
    wt = ProtheusWriteTracker(None)
    with pytest.raises(ProtheusRestError) as exc_info:
        wt.begin(**_tracker_kwargs())
    assert exc_info.value.code == "PROTHEUS_TRACKING_UNAVAILABLE"


def test_begin_sanitizes_stored_payloads() -> None:
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.begin_operation.return_value = "op-1"
    wt = ProtheusWriteTracker(tracker)
    wt.begin(
        **_tracker_kwargs(
            request_fields={"supplier_name": "ACME", "tax_id": "98887766000134"},
            outbound_body={"codusr": "000161", "fornecedor": {"phone": "1"}},
        )
    )
    data = tracker.begin_operation.call_args.kwargs
    assert data["request_payload"]["fields"]["tax_id"] == "[REDACTED]"
    assert data["request_payload"]["fields"]["supplier_name"] == "ACME"
    assert data["outbound_payload"]["body"]["codusr"] == "[REDACTED]"
    assert data["outbound_payload"]["body"]["fornecedor"]["phone"] == "[REDACTED]"


# -------------------------------------------------------- outcome classify


def test_record_send_failure_maps_timeout_to_unknown() -> None:
    tracker = MagicMock(spec=IntegrationTrackingService)
    wt = ProtheusWriteTracker(tracker)
    wt.record_send_failure(
        "op-1",
        ProtheusRestError("timeout", code="PROTHEUS_TIMEOUT", status_code=504),
    )
    tracker.mark_outcome_unknown.assert_called_once()
    tracker.record_rejected.assert_not_called()


def test_record_send_failure_maps_deterministic_to_rejected() -> None:
    tracker = MagicMock(spec=IntegrationTrackingService)
    wt = ProtheusWriteTracker(tracker)
    wt.record_send_failure(
        "op-1",
        ProtheusRestError(
            "mata020 falhou",
            code="PROTHEUS_SUPPLIER_WRITE_MATA020_FAILED",
            status_code=400,
        ),
    )
    tracker.record_rejected.assert_called_once()
    tracker.mark_outcome_unknown.assert_not_called()


def test_record_send_failure_maps_unexpected_to_unknown() -> None:
    tracker = MagicMock(spec=IntegrationTrackingService)
    wt = ProtheusWriteTracker(tracker)
    wt.record_send_failure("op-1", RuntimeError("socket died"))
    tracker.mark_outcome_unknown.assert_called_once()


def test_record_send_failure_never_reraises_tracking_error() -> None:
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.mark_outcome_unknown.side_effect = IntegrationTrackingError("db")
    wt = ProtheusWriteTracker(tracker)
    # Must not raise — operation stays SENDING (indeterminate), caller keeps
    # the original upstream error.
    wt.record_send_failure(
        "op-1",
        ProtheusRestError("timeout", code="PROTHEUS_TIMEOUT", status_code=504),
    )


# ------------------------------------------------------- confirm lifecycle


def test_tracker_confirm_promotes_to_confirmed_with_evidence() -> None:
    """Regression F4.3: confirm() must supply the required evidence argument.

    Uses the real IntegrationTrackingService over the in-memory repository —
    a spec'd MagicMock silently accepts the missing kwarg that caused
    `confirmation_record_failed` in production.
    """
    from tests.test_integration_tracking_service import (
        InMemoryIntegrationOperationRepository,
    )

    repo = InMemoryIntegrationOperationRepository()
    service = IntegrationTrackingService(repository=repo)
    wt = ProtheusWriteTracker(service)

    operation_id = wt.begin(**_tracker_kwargs())
    wt.record_ack(
        operation_id,
        upstream={"http_status": 200, "upstream": {"mensagem": "ok"}},
        resource_key="00387801",
    )
    assert wt.confirm(
        operation_id, checked_fields=["supplier_name"], result="MATCH"
    ) is True

    row = repo.get_operation(operation_id)
    assert row["status"] == "CONFIRMED"
    evidence = row["confirmation_evidence"]
    assert evidence["method"] == "READ_AFTER_WRITE"
    assert evidence["resource_key"] == "00387801"
    assert evidence["environment_key"] == "ambiente:1@host:8701"
    assert evidence["checked_fields"] == ["supplier_name"]
    assert evidence["result"] == "MATCH"
    assert evidence["schema_version"] == 1
    event_types = [
        e["event_type"]
        for e in repo.list_events(operation_id, limit=10, offset=0)
    ]
    assert event_types == [
        "operation_created",
        "send_started",
        "upstream_response",
        "status_transition",
    ]


def test_use_case_update_confirmed_with_real_tracker(monkeypatch) -> None:
    """End-to-end: UPDATE + matching GET promotes the operation to CONFIRMED."""
    from tests.test_integration_tracking_service import (
        InMemoryIntegrationOperationRepository,
    )

    _enable(monkeypatch)
    repo = InMemoryIntegrationOperationRepository()
    service = IntegrationTrackingService(repository=repo)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.update_supplier.return_value = {
        "write_outcome": "accepted_by_upstream",
        "update_acknowledged": True,
        "http_status": 200,
        "upstream": {"mensagem": "Fornecedor alterado com sucesso."},
    }
    gateway.get_supplier.return_value = {
        "fornecedor": {"supplier_short_name": "HOMOLOG X"}
    }

    result = _uc(
        identity_gateway=identity, gateway=gateway, tracker=service
    ).execute(
        actor_user_id=ACTOR,
        supplier_id="00387801",
        fornecedor={"supplier_short_name": "HOMOLOG X"},
        caller_app="supplies-api",
    )

    assert result["update_confirmed"] is True
    assert result["persistence_proven"] is True
    assert "tracking_warning" not in result
    operation_id = result["operation_id"]
    row = repo.get_operation(operation_id)
    assert row["status"] == "CONFIRMED"
    assert row["confirmation_evidence"]["checked_fields"] == [
        "supplier_short_name"
    ]
    assert row["attempt_count"] == 1
    assert gateway.update_supplier.call_count == 1


# ---------------------------------------------------------- use case wiring


def _uc(**overrides):
    params = MagicMock()
    params.load_raw_params.return_value = {}
    token = MagicMock()
    token.get_valid_token.return_value = "tok"
    kwargs = dict(
        params_repository=params,
        token_service=token,
        gateway=MagicMock(),
        identity_gateway=MagicMock(),
        tracker=MagicMock(spec=IntegrationTrackingService),
    )
    kwargs.update(overrides)
    return UpdateProtheusRestSupplierUseCase(**kwargs)


def _enable(monkeypatch):
    monkeypatch.setattr(
        "app.application.use_cases.integrations."
        "update_protheus_rest_supplier_use_case.settings",
        MagicMock(
            PROTHEUS_SUPPLIER_UPDATE_ENABLED=True,
            INTRANET_PARAMS_AMBIENTE="1",
        ),
    )
    monkeypatch.setattr(
        "app.application.use_cases.integrations."
        "update_protheus_rest_supplier_use_case.resolve_protheus_rest_config",
        lambda raw: _CONFIG,
    )


def test_use_case_fails_closed_when_tracking_unavailable(monkeypatch) -> None:
    _enable(monkeypatch)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.begin_operation.side_effect = IntegrationTrackingError("db down")

    with pytest.raises(ProtheusRestError) as exc_info:
        _uc(
            identity_gateway=identity, gateway=gateway, tracker=tracker
        ).execute(
            actor_user_id=ACTOR,
            supplier_id="00387801",
            fornecedor={"supplier_short_name": "X"},
        )
    assert exc_info.value.code == "PROTHEUS_TRACKING_UNAVAILABLE"
    gateway.update_supplier.assert_not_called()


def test_use_case_success_records_operation_and_returns_id(monkeypatch) -> None:
    _enable(monkeypatch)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.update_supplier.return_value = {
        "write_outcome": "accepted_by_upstream",
        "update_acknowledged": True,
        "http_status": 200,
        "upstream": {"mensagem": "Fornecedor alterado com sucesso."},
    }
    gateway.get_supplier.return_value = {
        "fornecedor": {"supplier_short_name": "HOMOLOG X"}
    }
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.begin_operation.return_value = "op-123"

    result = _uc(
        identity_gateway=identity, gateway=gateway, tracker=tracker
    ).execute(
        actor_user_id=ACTOR,
        supplier_id="00387801",
        fornecedor={"supplier_short_name": "HOMOLOG X"},
        caller_app="supplies-api",
        correlation_id="corr-9",
        request_id="req-9",
    )

    assert result["operation_id"] == "op-123"
    tracker.begin_operation.assert_called_once()
    tracker.mark_sending.assert_called_once_with("op-123")
    tracker.record_acknowledged.assert_called_once()
    # Read-after-write matched -> CONFIRMED.
    tracker.confirm.assert_called_once()
    assert result["persistence_proven"] is True
    assert result["update_confirmed"] is True
    assert gateway.update_supplier.call_count == 1


def test_use_case_timeout_marks_unknown_no_retry(monkeypatch) -> None:
    _enable(monkeypatch)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.update_supplier.side_effect = ProtheusRestError(
        "timeout", code="PROTHEUS_TIMEOUT", status_code=504
    )
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.begin_operation.return_value = "op-t"

    with pytest.raises(ProtheusRestError):
        _uc(
            identity_gateway=identity, gateway=gateway, tracker=tracker
        ).execute(
            actor_user_id=ACTOR,
            supplier_id="00387801",
            fornecedor={"supplier_short_name": "X"},
        )
    tracker.mark_outcome_unknown.assert_called_once()
    assert gateway.update_supplier.call_count == 1  # never retried


def test_use_case_deterministic_rejection_mapped(monkeypatch) -> None:
    _enable(monkeypatch)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.update_supplier.side_effect = ProtheusRestError(
        "mata020", code="PROTHEUS_SUPPLIER_UPDATE_MATA020_FAILED",
        status_code=400,
    )
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.begin_operation.return_value = "op-r"

    with pytest.raises(ProtheusRestError):
        _uc(
            identity_gateway=identity, gateway=gateway, tracker=tracker
        ).execute(
            actor_user_id=ACTOR,
            supplier_id="00387801",
            fornecedor={"supplier_short_name": "X"},
        )
    tracker.record_rejected.assert_called_once()
    tracker.mark_outcome_unknown.assert_not_called()


def test_use_case_mismatch_flags_reconciliation(monkeypatch) -> None:
    _enable(monkeypatch)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.update_supplier.return_value = {
        "write_outcome": "accepted_by_upstream",
        "update_acknowledged": True,
        "http_status": 200,
        "upstream": {},
    }
    gateway.get_supplier.return_value = {
        "fornecedor": {"supplier_short_name": "DIFFERENT VALUE"}
    }
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.begin_operation.return_value = "op-m"

    result = _uc(
        identity_gateway=identity, gateway=gateway, tracker=tracker
    ).execute(
        actor_user_id=ACTOR,
        supplier_id="00387801",
        fornecedor={"supplier_short_name": "HOMOLOG X"},
    )
    tracker.require_reconciliation.assert_called_once()
    tracker.confirm.assert_not_called()
    assert result["persistence_proven"] is False
    assert result["tracking_warning"] == "confirmation_mismatch"


def test_confirmation_read_failure_keeps_acknowledged(monkeypatch) -> None:
    _enable(monkeypatch)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.update_supplier.return_value = {
        "write_outcome": "accepted_by_upstream",
        "update_acknowledged": True,
        "http_status": 200,
        "upstream": {},
    }
    gateway.get_supplier.side_effect = ProtheusRestError(
        "unavail", code="PROTHEUS_UNAVAILABLE", status_code=502
    )
    tracker = MagicMock(spec=IntegrationTrackingService)
    tracker.begin_operation.return_value = "op-c"

    result = _uc(
        identity_gateway=identity, gateway=gateway, tracker=tracker
    ).execute(
        actor_user_id=ACTOR,
        supplier_id="00387801",
        fornecedor={"supplier_short_name": "X"},
    )
    tracker.confirm.assert_not_called()
    tracker.record_confirmation_failure.assert_called_once()
    assert result["persistence_proven"] is False


# ---------------------------------------------------------- compare helpers


def test_compare_sent_fields_tolerant() -> None:
    sent = {"supplier_short_name": "ABC", "district": "CENTRO"}
    read = {"supplier_short_name": " ABC ", "district": "CENTRO", "extra": 1}
    out = compare_sent_fields(sent, read)
    assert out["mismatched"] == []
    assert set(out["matched"]) == {"supplier_short_name", "district"}


def test_compare_detects_mismatch_and_missing() -> None:
    sent = {"supplier_short_name": "ABC", "phone": "1"}
    read = {"supplier_short_name": "XYZ"}
    out = compare_sent_fields(sent, read)
    assert out["mismatched"] == ["supplier_short_name"]
    assert out["missing"] == ["phone"]


def test_extract_supplier_fields_shapes() -> None:
    assert extract_supplier_fields({"fornecedor": {"a": 1}}) == {"a": 1}
    assert extract_supplier_fields({"supplier": {"b": 2}}) == {"b": 2}
    assert extract_supplier_fields({"a": 1}) == {"a": 1}
    assert extract_supplier_fields("junk") == {}
