from __future__ import annotations

from unittest.mock import patch

from app.application.services.home_attention_service import HomeAttentionService
from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser


def _user(*, permissions: set[str], is_superadmin: bool = False) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
        is_superadmin=is_superadmin,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


def _identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer",
    )


def test_compose_portal_and_operations_includes_ops_cards():
    user = _user(
        permissions={
            "supplies.portal.access",
            "supplies.operations.access",
        }
    )
    result = HomeAttentionService().compose(user)
    ids = [card["id"] for card in result["cards"]]
    assert "my_tasks" in ids
    assert "purchase_orders" in ids
    assert "deliveries" in ids
    assert "safety_stock" in ids
    assert "overview" not in ids
    assert "purchase_requests" not in ids
    assert all(card["count"] is None for card in result["cards"])
    assert all(card["status"] == "available" for card in result["cards"])
    assert result["partialFailures"] == []


def test_compose_portal_only_omits_domain_cards():
    user = _user(permissions={"supplies.portal.access"})
    result = HomeAttentionService().compose(user)
    ids = [card["id"] for card in result["cards"]]
    assert ids == ["my_tasks"]
    assert result["partialFailures"] == []


def test_compose_superadmin_gets_all_cards():
    user = _user(permissions=set(), is_superadmin=True)
    result = HomeAttentionService().compose(user)
    ids = {card["id"] for card in result["cards"]}
    assert {
        "my_tasks",
        "purchase_requests",
        "purchase_orders",
        "deliveries",
        "safety_stock",
        "overview",
        "administration",
    } <= ids


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_home_attention_positive(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.portal.access",
            "supplies.operations.access",
        }
    )
    client = create_app().test_client()
    response = client.get(
        "/home/attention",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert "cards" in body
    assert body["partialFailures"] == []
    assert any(card["id"] == "purchase_orders" for card in body["cards"])


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_home_attention_sibling_portal_only(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.portal.access"})
    client = create_app().test_client()
    response = client.get(
        "/home/attention",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 200
    ids = [card["id"] for card in response.get_json()["cards"]]
    assert ids == ["my_tasks"]


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_home_attention_forbidden_without_portal(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.analytics.access"})
    client = create_app().test_client()
    response = client.get(
        "/home/attention",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 403
