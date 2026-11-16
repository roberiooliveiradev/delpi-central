from unittest.mock import patch

import pytest

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


@pytest.fixture()
def client():
    application = create_app()
    application.config["TESTING"] = True
    with application.test_client() as client:
        yield client


def auth(permissions=None):
    identity = AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer",
    )
    user = EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email=identity.email,
        name=identity.name,
        permissions=permissions if permissions is not None else {"supplies.access"},
        is_superadmin=False,
        keycloak_sub=identity.sub,
        access_token="user-jwt",
    )
    return patch(
        "app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate",
        return_value=identity,
    ), patch(
        "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user",
        return_value=user,
    )


URL = "/analytics/supplier-performance?branch=01&branch=02&date_from=2026-11-01&date_to=2026-11-16"
HEADERS = {"Authorization": "Bearer token"}
COMPONENT = dict(
    index=80.0,
    assessed_count=10,
    positive_count=8,
    negative_count=2,
    unknown_count=0,
    conditional_count=1,
    urgent_count=1,
)
PAYLOAD = dict(
    items=[
        dict(
            supplier_code="000001",
            supplier_store="01",
            supplier_name="Teste",
            branches=["01"],
            quality=COMPONENT,
            delivery=COMPONENT,
            idf=80.0,
            quality_contribution=56.0,
            delivery_contribution=24.0,
            status="complete",
        )
    ],
    summary=dict(
        suppliers=1,
        evaluated=1,
        incomplete=0,
        average_idf=80.0,
        average_quality=80.0,
        average_delivery=80.0,
        inspection_count=10,
        receipt_count=10,
    ),
    methodology=dict(
        quality_weight=70, delivery_weight=30, scale=100, classification_bands=None
    ),
    period={"from": "2026-11-01", "to": "2026-11-16"},
    branches=["01", "02"],
    calculated_at="2026-11-16T08:00:00-03:00",
)


def test_unauthenticated_401(client):
    assert client.get(URL).status_code == 401


@pytest.mark.parametrize("permissions", [set(), {"supplies.manage"}])
def test_no_normal_access_never_calls_upstream(client, permissions):
    validate, resolve = auth(permissions)
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        assert client.get(URL, headers=HEADERS).status_code == 403
        gateway.get.assert_not_called()


@pytest.mark.parametrize(
    "url",
    [
        URL.replace("branch=01&branch=02&", ""),
        URL.replace("branch=02", "branch=03"),
        URL.replace("branch=02", "branch=01,02"),
    ],
)
def test_missing_or_invalid_branch_fail_closed(client, url):
    validate, resolve = auth()
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        assert client.get(url, headers=HEADERS).status_code == 403
        gateway.get.assert_not_called()


def test_repeated_branches_delegate_user_token_and_unwrap(client):
    validate, resolve = auth()
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        gateway.get.return_value = {"success": True, "data": PAYLOAD}
        response = client.get(URL, headers=HEADERS)
        assert response.status_code == 200
        assert response.get_json() == PAYLOAD
        gateway.get.assert_called_once_with(
            "/supplies/supplier-performance",
            access_token="user-jwt",
            params=[
                ("branch", "01"),
                ("branch", "02"),
                ("date_from", "2026-11-01"),
                ("date_to", "2026-11-16"),
            ],
        )


@pytest.mark.parametrize("suffix", ["&unexpected=true", "&date_from=2026-01-01"])
def test_unsupported_or_ambiguous_filters_422(client, suffix):
    validate, resolve = auth()
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        assert client.get(URL + suffix, headers=HEADERS).status_code == 422
        gateway.get.assert_not_called()


@pytest.mark.parametrize(
    "upstream,status", [(403, 403), (422, 422), (503, 502), (None, 502)]
)
def test_upstream_errors_are_safe_not_empty_success(client, upstream, status):
    validate, resolve = auth()
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        gateway.get.side_effect = DelpiApiGatewayError(
            "secret details", status_code=upstream
        )
        response = client.get(URL, headers=HEADERS)
        assert response.status_code == status
        assert b"secret details" not in response.data


@pytest.mark.parametrize(
    "payload",
    [
        {},
        dict(PAYLOAD, period={}),
        dict(PAYLOAD, methodology={}),
        {"items": [], "summary": {}},
        dict(PAYLOAD, items=[dict(PAYLOAD["items"][0], quality={})]),
    ],
)
def test_malformed_payload_is_502(client, payload):
    validate, resolve = auth()
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        gateway.get.return_value = {"success": True, "data": payload}
        assert client.get(URL, headers=HEADERS).status_code == 502
