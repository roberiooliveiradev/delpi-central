"""Route-level provenance contract — optional change_context on POST/PUT and
the scoped provenance read route."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import UUID

import pytest

from app.application.security import api_delpi_permissions as perms
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.interface.http import s2s_service_access
from app.interface.http.routes.integrations import protheus_router

ACTOR = "401b25fa-ccd1-4800-8a12-a767909956b4"


def _user(*permission_codes: str):
    return SimpleNamespace(
        id=ACTOR,
        name="Tester",
        is_superadmin=False,
        permissions=list(permission_codes),
    )


def _request(service_identity=None, actor=None):
    return SimpleNamespace(
        state=SimpleNamespace(service_identity=service_identity, user=actor),
        headers={},
    )


def _body(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


def _s2s_invoke(handler, *args, **kwargs):
    """Invoke a decorated route; return kwargs used on validator.validate."""
    validator = Mock()
    validator.validate.return_value = SimpleNamespace(
        client_id="supplies-api",
        subject="svc",
        scopes=frozenset({"suppliers.read"}),
        audience=("api-delpi",),
        issuer="x",
    )
    with (
        patch.object(
            s2s_service_access,
            "get_request",
            return_value=SimpleNamespace(
                headers={"X-Delpi-Service-Authorization": "Bearer t"},
                state=SimpleNamespace(),
            ),
        ),
        patch.object(
            s2s_service_access.ServiceTokenValidator,
            "from_env",
            return_value=validator,
        ),
    ):
        try:
            handler(*args, **kwargs)
        except Exception:
            pass
    assert validator.validate.called
    return validator.validate.call_args.kwargs


def test_provenance_route_declares_read_scope() -> None:
    kwargs = _s2s_invoke(
        protheus_router.list_supplier_field_provenance_route,
        request=_request(),
        supplier_id="00387801",
    )
    assert kwargs["required_scopes"] == ("suppliers.read",)
    assert kwargs["allowed_clients"] == ("supplies-api",)


def test_update_forwards_change_context_to_use_case() -> None:
    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_SUPPLIERS_UPDATE)
    context = {
        "schema_version": "1",
        "change_mode": "MANUAL_DIRECT",
        "field_provenance": [
            {"field_key": "supplier_name", "source_type": "MANUAL_USER_INPUT"}
        ],
    }
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.build_update_protheus_rest_supplier_use_case"
    ) as build_uc:
        build_uc.return_value.execute.side_effect = ProtheusRestError(
            "gate off",
            code="PROTHEUS_SUPPLIER_UPDATE_DISABLED",
            status_code=503,
            recoverable=False,
        )
        protheus_router.update_protheus_rest_supplier_route(
            request=_request(),
            supplier_id="00387801",
            body={
                "fornecedor": {"supplier_name": "X"},
                "change_context": context,
            },
        )
    kwargs = build_uc.return_value.execute.call_args.kwargs
    assert kwargs["change_context"] == context


def test_update_rejects_non_object_change_context() -> None:
    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_SUPPLIERS_UPDATE)
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.get_current_user",
        return_value=user,
    ):
        response = protheus_router.update_protheus_rest_supplier_route(
            request=_request(),
            supplier_id="00387801",
            body={
                "fornecedor": {"supplier_name": "X"},
                "change_context": ["not-an-object"],
            },
        )
    assert _body(response)["error"]["code"] == "PROVENANCE_CONTEXT_INVALID"


def test_create_forwards_change_context_to_use_case() -> None:
    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_SUPPLIERS_CREATE)
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.build_create_protheus_rest_supplier_use_case"
    ) as build_uc:
        build_uc.return_value.execute.return_value = {
            "creation_confirmed": False
        }
        protheus_router.create_protheus_rest_supplier_route(
            request=_request(),
            body={
                "fornecedor": {"supplier_name": "X"},
                "change_context": {
                    "schema_version": "1",
                    "change_mode": "MANUAL_DIRECT",
                    "field_provenance": [
                        {
                            "field_key": "supplier_name",
                            "source_type": "MANUAL_USER_INPUT",
                        }
                    ],
                },
            },
        )
    kwargs = build_uc.return_value.execute.call_args.kwargs
    assert kwargs["change_context"]["change_mode"] == "MANUAL_DIRECT"
    assert kwargs["actor_user_id"] == UUID(ACTOR)


def test_provenance_read_binds_s2s_caller_identity() -> None:
    service = Mock()
    service.list_supplier_provenance.return_value = {
        "supplier_id": "00387801",
        "fields": [],
        "attempts": [],
        "page": {"limit": 100, "offset": 0},
    }
    identity = SimpleNamespace(client_id="supplies-api")
    actor = SimpleNamespace(id=ACTOR)
    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.build_integration_tracking_service",
        return_value=service,
    ):
        response = protheus_router.list_supplier_field_provenance_route(
            request=_request(service_identity=identity, actor=actor),
            supplier_id="00387801",
            field_key="supplier_name",
        )
    body = _body(response)
    assert body["meta"]["operationId"] == "list_supplier_field_provenance"
    kwargs = service.list_supplier_provenance.call_args.kwargs
    assert kwargs["caller_app"] == "supplies-api"
    assert kwargs["actor_subject"] == ACTOR
    assert kwargs["supplier_id"] == "00387801"
    assert kwargs["field_key"] == "supplier_name"


def test_provenance_read_denied_without_permission() -> None:
    user = _user("some.other.permission")
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ):
        with pytest.raises(Exception, match="Forbidden"):
            protheus_router.list_supplier_field_provenance_route(
                request=_request(),
                supplier_id="00387801",
            )


def test_openapi_includes_provenance_operation() -> None:
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(protheus_router.router)
    schema = app.openapi()
    path = schema["paths"][
        "/integrations/protheus/suppliers/{supplier_id}/provenance"
    ]
    assert path["get"]["operationId"] == "list_supplier_field_provenance"
