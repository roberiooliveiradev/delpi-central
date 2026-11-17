"""HTTP route tests — product PUT AuthZ is independent from supplier writes."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

import pytest

from app.application.security import api_delpi_permissions as perms
from app.domain.integrations.protheus_rest import ProtheusRestError


def _user(*permission_codes: str):
    return SimpleNamespace(
        id="401b25fa-ccd1-4800-8a12-a767909956b4",
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


def test_read_permission_cannot_update_product() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        update_protheus_product_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        with pytest.raises(Exception, match="Forbidden"):
            update_protheus_product_route(
                request=_fake_request(),
                product_code="ABC123",
                body={"B1_DESC": "X"},
            )


def test_supplier_update_permission_cannot_update_product() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        update_protheus_product_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_SUPPLIERS_UPDATE)
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        with pytest.raises(Exception, match="Forbidden"):
            update_protheus_product_route(
                request=_fake_request(),
                product_code="ABC123",
                body={"B1_DESC": "X"},
            )


def test_rejects_client_codusr() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        update_protheus_product_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_PRODUCTS_UPDATE)
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.get_current_user",
        return_value=user,
    ):
        response = update_protheus_product_route(
            request=_fake_request(),
            product_code="ABC123",
            body={"codusr": "000999", "B1_DESC": "X"},
        )
    assert _body(response)["error"]["code"] == "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN"


def test_gate_disabled_envelope() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        update_protheus_product_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_PRODUCTS_UPDATE)
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.build_update_protheus_product_use_case"
    ) as build_uc:
        build_uc.return_value.execute.side_effect = ProtheusRestError(
            "off",
            code="PROTHEUS_PRODUCT_UPDATE_DISABLED",
            status_code=503,
            recoverable=False,
        )
        response = update_protheus_product_route(
            request=_fake_request(),
            product_code="ABC123",
            body={"B1_DESC": "X"},
        )
    body = _body(response)
    assert body["error"]["code"] == "PROTHEUS_PRODUCT_UPDATE_DISABLED"
    kwargs = build_uc.return_value.execute.call_args.kwargs
    assert kwargs["actor_user_id"] == UUID("401b25fa-ccd1-4800-8a12-a767909956b4")
    assert kwargs["product_code"] == "ABC123"


def test_openapi_product_update_operation_unique() -> None:
    from fastapi import FastAPI

    from app.interface.http.routes.integrations.protheus_router import router

    app = FastAPI()
    app.include_router(router)
    schema = app.openapi()
    op = schema["paths"]["/integrations/protheus/products/{product_code}"]["put"]
    assert op["operationId"] == "update_protheus_product"
    ids = [
        item.get("operationId")
        for path in schema["paths"].values()
        for item in path.values()
        if isinstance(item, dict) and item.get("operationId")
    ]
    assert ids.count("update_protheus_product") == 1
