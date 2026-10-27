"""UX-009 — Core person-profile gateway: transporte S2S honesto.

Foto 404/indisponível → ``None`` (fallback do consumidor); conteúdo
não-imagem ou grande demais → ``None``; lookup falha → ``{}``. O
gateway nunca inventa perfil nem monta URL por convenção.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from controllership_finance_app.infrastructure.gateways.core_person_profile_gateway import (  # noqa: E501
    CorePersonProfileGateway,
)

USER_A = "11111111-2222-3333-4444-555555555555"


@pytest.fixture(autouse=True)
def _service_token(monkeypatch):
    monkeypatch.setattr(
        "controllership_finance_app.infrastructure.gateways."
        "core_person_profile_gateway.settings",
        MagicMock(
            CORE_API_BASE_URL="http://core:8000",
            CORE_API_INTEGRATIONS_SERVICE_TOKEN="svc-token",
        ),
    )


def _response(
    status: int = 200,
    *,
    content: bytes = b"",
    headers: dict | None = None,
    json_payload: dict | None = None,
) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.content = content
    resp.headers = headers or {}
    resp.json.return_value = json_payload or {}
    resp.raise_for_status = MagicMock()
    if status >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "err", request=MagicMock(), response=resp
        )
    return resp


def test_configured_requires_url_and_token():
    gw = CorePersonProfileGateway(base_url="http://core:8000")
    assert gw.configured() is True


def test_get_photo_returns_bytes_and_type():
    gw = CorePersonProfileGateway()
    with patch(
        "controllership_finance_app.infrastructure.gateways."
        "core_person_profile_gateway.httpx.get"
    ) as get:
        get.return_value = _response(
            200,
            content=b"\xff\xd8\xffjpg",
            headers={"content-type": "image/jpeg"},
        )
        photo = gw.get_photo(USER_A)
    assert photo == (b"\xff\xd8\xffjpg", "image/jpeg", "photo.bin")
    called_url = get.call_args[0][0]
    assert f"/integrations/person-profiles/{USER_A}/photo" in called_url


def test_get_photo_404_is_none():
    gw = CorePersonProfileGateway()
    with patch(
        "controllership_finance_app.infrastructure.gateways."
        "core_person_profile_gateway.httpx.get"
    ) as get:
        get.return_value = _response(404)
        assert gw.get_photo(USER_A) is None


def test_get_photo_rejects_non_image_content_type():
    gw = CorePersonProfileGateway()
    with patch(
        "controllership_finance_app.infrastructure.gateways."
        "core_person_profile_gateway.httpx.get"
    ) as get:
        get.return_value = _response(
            200,
            content=b"<html>nope</html>",
            headers={"content-type": "text/html"},
        )
        assert gw.get_photo(USER_A) is None


def test_get_photo_rejects_oversized():
    gw = CorePersonProfileGateway()
    with patch(
        "controllership_finance_app.infrastructure.gateways."
        "core_person_profile_gateway.httpx.get"
    ) as get:
        get.return_value = _response(
            200,
            content=b"x" * (2 * 1024 * 1024 + 1),
            headers={"content-type": "image/png"},
        )
        assert gw.get_photo(USER_A) is None


def test_get_photo_network_error_is_none():
    gw = CorePersonProfileGateway()
    with patch(
        "controllership_finance_app.infrastructure.gateways."
        "core_person_profile_gateway.httpx.get",
        side_effect=httpx.ConnectError("down"),
    ):
        assert gw.get_photo(USER_A) is None


def test_lookup_has_photo_merges_items():
    gw = CorePersonProfileGateway()
    with patch(
        "controllership_finance_app.infrastructure.gateways."
        "core_person_profile_gateway.httpx.post"
    ) as post:
        post.return_value = _response(
            200,
            json_payload={
                "items": [
                    {"user_id": USER_A, "has_photo": True},
                    {"user_id": "other", "has_photo": False},
                ]
            },
        )
        result = gw.lookup_has_photo([USER_A])
    assert result == {USER_A: True, "other": False}


def test_lookup_has_photo_failure_is_empty():
    gw = CorePersonProfileGateway()
    with patch(
        "controllership_finance_app.infrastructure.gateways."
        "core_person_profile_gateway.httpx.post"
    ) as post:
        post.return_value = _response(500)
        assert gw.lookup_has_photo([USER_A]) == {}


def test_lookup_directory_names_uses_caller_bearer():
    gw = CorePersonProfileGateway()
    with patch(
        "controllership_finance_app.infrastructure.gateways."
        "core_person_profile_gateway.httpx.post"
    ) as post:
        post.return_value = _response(
            200,
            json_payload={
                "items": [{"id": USER_A, "name": "Robério Oliveira"}]
            },
        )
        result = gw.lookup_directory_names(
            [USER_A], bearer_token="Bearer user-jwt"
        )
    assert result == {USER_A: "Robério Oliveira"}
    headers = post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer user-jwt"
    url = post.call_args[0][0]
    assert "/me/directory/users/lookup" in url


def test_lookup_directory_names_without_bearer_is_empty():
    gw = CorePersonProfileGateway()
    assert gw.lookup_directory_names([USER_A], bearer_token="") == {}
