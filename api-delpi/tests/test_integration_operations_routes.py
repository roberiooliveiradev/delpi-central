"""HTTP route tests — integration operations query AuthZ and projection."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from app.application.security import api_delpi_permissions as perms
from app.domain.integrations.integration_operation import (
    IntegrationTrackingError,
)

OP_ID = "e5de0688-852c-4f9b-ab77-87ed2809ec99"
ACTOR = "401b25fa-ccd1-4800-8a12-a767909956b4"


def _user(*permission_codes: str, user_id: str = ACTOR):
    return SimpleNamespace(
        id=user_id,
        name="Tester",
        is_superadmin=False,
        permissions=list(permission_codes),
    )


def _fake_request(*, caller_app=None, actor=ACTOR):
    service_identity = (
        SimpleNamespace(client_id=caller_app) if caller_app else None
    )
    return SimpleNamespace(
        state=SimpleNamespace(
            service_identity=service_identity,
            user=SimpleNamespace(id=actor),
        ),
        headers={},
    )


def _body(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


def _op(**overrides):
    op = {
        "operation_id": OP_ID,
        "integration": "protheus",
        "resource": "supplier",
        "action": "update",
        "status": "CONFIRMED",
        "caller_app": "supplies-api",
        "actor_subject": ACTOR,
        "resource_key": "00387801",
        "environment_key": "ambiente:1@h:8701",
        "correlation_id": "c",
        "request_payload": {"schema_version": 1, "fields": {"supplier_name": "X"}},
        "response_payload": {"schema_version": 1, "http_status": 200},
        "error_details": None,
        "confirmation_evidence": {"result": "MATCH"},
        "http_status": 200,
        "upstream_error_code": None,
        "attempt_count": 1,
        "created_at": "2026-10-21T00:00:00Z",
        "send_started_at": None,
        "acknowledged_at": None,
        "confirmed_at": "2026-10-21T00:00:01Z",
        "updated_at": "2026-10-21T00:00:01Z",
    }
    op.update(overrides)
    return op


def _service(**overrides):
    """Tracking service stub — MagicMock recusa attrs iniciados em 'assert'."""
    defaults = dict(
        get_operation=lambda oid: _op(),
        assert_can_view=lambda op, caller_app=None, actor_subject=None: None,
        list_events=lambda oid, limit=100, offset=0: [],
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _deny(op, caller_app=None, actor_subject=None):
    raise IntegrationTrackingError(
        "forbidden", code="INTEGRATION_OPERATION_FORBIDDEN"
    )


def _route_patches(user):
    return (
        patch(
            "delpi_auth.authorization.resolve_user_context",
            return_value=user,
        ),
        patch(
            "app.interface.http.routes.integrations.integration_operations_router"
            ".get_current_user",
            return_value=user,
            create=True,
        ),
    )


def test_invalid_uuid_rejected() -> None:
    from app.interface.http.routes.integrations.integration_operations_router import (
        get_integration_operation_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    p1, p2 = _route_patches(user)
    with p1, p2:
        response = get_integration_operation_route(
            request=_fake_request(caller_app="supplies-api"),
            operation_id="not-a-uuid",
        )
    assert _body(response)["error"]["code"] == "PROTHEUS_OPERATION_ID_INVALID"


def test_unknown_operation_is_404() -> None:
    from app.interface.http.routes.integrations import (
        integration_operations_router as module,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    service = _service(get_operation=lambda oid: None)
    p1, p2 = _route_patches(user)
    with p1, p2, patch.object(
        module, "build_integration_tracking_service", return_value=service
    ):
        response = module.get_integration_operation_route(
            request=_fake_request(caller_app="supplies-api"),
            operation_id=OP_ID,
        )
    assert _body(response)["error"]["code"] == "PROTHEUS_OPERATION_NOT_FOUND"


def test_other_caller_app_forbidden() -> None:
    from app.interface.http.routes.integrations import (
        integration_operations_router as module,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    service = _service(assert_can_view=_deny)
    p1, p2 = _route_patches(user)
    with p1, p2, patch.object(
        module, "build_integration_tracking_service", return_value=service
    ):
        response = module.get_integration_operation_route(
            request=_fake_request(caller_app="other-app"),
            operation_id=OP_ID,
        )
    body = _body(response)
    assert body["error"]["code"] == "INTEGRATION_OPERATION_FORBIDDEN"


def test_other_actor_forbidden() -> None:
    from app.interface.http.routes.integrations import (
        integration_operations_router as module,
    )

    user = _user(
        perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ, user_id="other-user"
    )
    service = _service(assert_can_view=_deny)
    p1, p2 = _route_patches(user)
    with p1, p2, patch.object(
        module, "build_integration_tracking_service", return_value=service
    ):
        response = module.get_integration_operation_route(
            request=_fake_request(caller_app="supplies-api", actor="other-user"),
            operation_id=OP_ID,
        )
    assert _body(response)["error"]["code"] == "INTEGRATION_OPERATION_FORBIDDEN"


def test_authorized_read_projects_safe_fields_only() -> None:
    from app.interface.http.routes.integrations import (
        integration_operations_router as module,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    service = _service(
        get_operation=lambda oid: _op(
            outbound_payload={"body": {"codusr": "000311"}},
            protheus_user_id="000311",
            request_hash="h" * 64,
            authorization_context="internal",
        )
    )
    p1, p2 = _route_patches(user)
    with p1, p2, patch.object(
        module, "build_integration_tracking_service", return_value=service
    ):
        response = module.get_integration_operation_route(
            request=_fake_request(caller_app="supplies-api"),
            operation_id=OP_ID,
        )
    body = _body(response)
    assert body["success"] is True
    data = body["data"]
    assert data["operation_id"] == OP_ID
    assert data["status"] == "CONFIRMED"
    # Internal-only fields are not projected to the consumer.
    for hidden in (
        "outbound_payload",
        "protheus_user_id",
        "request_hash",
        "outbound_hash",
        "authorization_context",
        "actor_subject",
        "caller_app",
    ):
        assert hidden not in data


def test_events_route_returns_ordered_events() -> None:
    from app.interface.http.routes.integrations import (
        integration_operations_router as module,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    service = _service(
        list_events=lambda oid, limit=100, offset=0: [
            {"sequence_number": 1, "event_type": "operation_created"},
            {"sequence_number": 2, "event_type": "send_started"},
        ]
    )
    p1, p2 = _route_patches(user)
    with p1, p2, patch.object(
        module, "build_integration_tracking_service", return_value=service
    ):
        response = module.list_integration_operation_events_route(
            request=_fake_request(caller_app="supplies-api"),
            operation_id=OP_ID,
            limit=50,
            offset=0,
        )
    body = _body(response)
    assert body["success"] is True
    seqs = [e["sequence_number"] for e in body["data"]["events"]]
    assert seqs == sorted(seqs)
