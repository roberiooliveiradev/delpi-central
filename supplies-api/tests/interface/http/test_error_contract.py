from unittest.mock import patch

from flask import jsonify

from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.interfaces.http.auth_decorators import require_permission


def test_not_found_envelope_after_auth(client):
    with patch(
        "app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate",
        return_value=AuthenticatedIdentity(
            sub="11111111-1111-1111-1111-111111111111",
            email="a@delpi.com.br",
        ),
    ), patch(
        "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user",
        return_value=EffectiveUser(
            id="22222222-2222-2222-2222-222222222222",
            email="a@delpi.com.br",
            name=None,
            permissions={"supplies.portal.access"},
        ),
    ):
        response = client.get(
            "/does-not-exist",
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 404
    body = response.get_json()
    assert body["code"] == "not_found"
    assert "detail" in body


def test_forbidden_envelope_has_code(app):
    @app.get("/_test/forbidden-envelope")
    @require_permission("supplies.portal.access")
    def secure():
        return jsonify({"ok": True}), 200

    with app.test_client() as client, patch(
        "app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate",
        return_value=AuthenticatedIdentity(
            sub="11111111-1111-1111-1111-111111111111",
            email="a@delpi.com.br",
        ),
    ), patch(
        "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user",
        return_value=EffectiveUser(
            id="22222222-2222-2222-2222-222222222222",
            email="a@delpi.com.br",
            name=None,
            permissions=set(),
        ),
    ):
        response = client.get(
            "/_test/forbidden-envelope",
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 403
    assert response.get_json()["code"] == "forbidden"
