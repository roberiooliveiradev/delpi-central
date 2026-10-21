"""HTTP route tests — AuthZ, feature gate, identity impersonation rejection."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

import pytest

from app.application.security import api_delpi_permissions as perms
from app.domain.integrations.protheus_rest import ProtheusRestError


def _user(*permission_codes: str, user_id: str = "401b25fa-ccd1-4800-8a12-a767909956b4"):
    return SimpleNamespace(
        id=user_id,
        name="Tester",
        is_superadmin=False,
        permissions=list(permission_codes),
    )


def _fake_request():
    return SimpleNamespace(
        state=SimpleNamespace(service_identity=None),
        headers={},
    )


def _body(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


def test_create_forbidden_without_permission() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        create_protheus_rest_supplier_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        with pytest.raises(Exception, match="Forbidden"):
            create_protheus_rest_supplier_route(
            request=_fake_request(),
                body={"fornecedor": {"supplier_store": "01"}}
            )


def test_create_forbidden_with_data_permission() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        create_protheus_rest_supplier_route,
    )

    user = _user(perms.API_DELPI_DATA)
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        with pytest.raises(Exception, match="Forbidden"):
            create_protheus_rest_supplier_route(
            request=_fake_request(),
                body={"fornecedor": {"supplier_store": "01"}}
            )


def test_create_rejects_client_codusr() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        create_protheus_rest_supplier_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_SUPPLIERS_CREATE)
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.get_current_user",
        return_value=user,
    ):
        response = create_protheus_rest_supplier_route(
            request=_fake_request(),
            body={
                "codusr": "000161",
                "fornecedor": {"supplier_store": "01"},
            }
        )
    body = _body(response)
    assert body["success"] is False
    assert body["error"]["code"] == "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN"


def test_create_feature_gate_disabled_no_upstream() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        create_protheus_rest_supplier_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_SUPPLIERS_CREATE)
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.build_create_protheus_rest_supplier_use_case"
    ) as build_uc:
        build_uc.return_value.execute.side_effect = ProtheusRestError(
            "disabled",
            code="PROTHEUS_SUPPLIER_CREATE_DISABLED",
            status_code=503,
            recoverable=False,
        )
        response = create_protheus_rest_supplier_route(
            request=_fake_request(),
            body={"fornecedor": {"supplier_store": "01"}}
        )
    body = _body(response)
    assert body["success"] is False
    assert body["error"]["code"] == "PROTHEUS_SUPPLIER_CREATE_DISABLED"
    build_uc.return_value.execute.assert_called_once()
    kwargs = build_uc.return_value.execute.call_args.kwargs
    assert kwargs["actor_user_id"] == UUID("401b25fa-ccd1-4800-8a12-a767909956b4")


def test_create_authorized_success_envelope() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        create_protheus_rest_supplier_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_SUPPLIERS_CREATE)
    payload = {
        "codusr": "000161",
        "supplier_store": "01",
        "write_outcome": "accepted_by_upstream",
        "creation_confirmed": False,
        "supplier_code": None,
        "upstream": {"message": "ok"},
    }
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.build_create_protheus_rest_supplier_use_case"
    ) as build_uc:
        build_uc.return_value.execute.return_value = payload
        response = create_protheus_rest_supplier_route(
            request=_fake_request(),
            body={"fornecedor": {"supplier_store": "01"}}
        )
    body = _body(response)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "create_protheus_rest_supplier"
    assert body["data"]["codusr"] == "000161"
    assert "password" not in json.dumps(body).lower()


def test_openapi_includes_create_operation() -> None:
    from fastapi import FastAPI

    from app.interface.http.routes.integrations.protheus_router import router

    app = FastAPI()
    app.include_router(router)
    schema = app.openapi()
    paths = schema["paths"]
    assert "/integrations/protheus/suppliers" in paths
    assert "post" in paths["/integrations/protheus/suppliers"]
    op = paths["/integrations/protheus/suppliers"]["post"]
    assert op["operationId"] == "create_protheus_rest_supplier"
    # uniqueness
    ids = [
        item.get("operationId")
        for path in paths.values()
        for item in path.values()
        if isinstance(item, dict)
    ]
    assert ids.count("create_protheus_rest_supplier") == 1
