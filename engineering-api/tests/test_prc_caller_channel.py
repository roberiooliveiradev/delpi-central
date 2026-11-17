"""PRC-AUDIT-CHANNEL — canal de auditoria por superfície.

O ``X-Delpi-Caller-App`` que cada MFE já envia passa a ser capturado
pelo middleware compartilhado em contextvar e o ``_actor`` deriva o
``channel`` gravado em ``metadata.channel`` dos eventos do ledger:
``my-requests`` → ``my_requests``, ``engineering`` → ``engineering``,
ausente/desconhecido → ``portal`` (legado). EVA segue ``eva`` via
``prc_semantic`` (não coberto aqui — não passa pelo HTTP middleware).

Também cobre o BFF ``/v1/participants/*``: gate ``engineering.access``
e degradação honesta (404 → iniciais no MFE) quando a Core não tem foto.
"""

from __future__ import annotations

import pytest

from tests.conftest import rbac_payload
from tests.test_product_registration import (  # noqa: F401
    ANALYST,
    _create_body,
    _get,
    _post,
    _token,
    prc_service_repo,
)

_BASE = "/v1/product-registration/requests"


def _as(jwks_env, core_rbac, perms, sub):
    core_rbac["behavior"] = ("data", rbac_payload(perms, id=sub))
    return _token(jwks_env, sub)


def _intake(client, jwks_env, core_rbac, caller_app, sub="user-1"):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    headers = {"Idempotency-Key": "k-1"}
    if caller_app is not None:
        headers["X-Delpi-Caller-App"] = caller_app
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env, sub),
        json=_create_body(),
        headers=headers,
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["data"]["requestId"]


def _first_channel(client, token, rid):
    resp = _get(client, f"{_BASE}/{rid}/timeline", token)
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]["items"]
    assert items, "timeline vazia após intake"
    return (items[0].get("metadata") or {}).get("channel")


class TestCallerAppChannel:
    def test_my_requests_caller_records_my_requests_channel(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        tok = _as(jwks_env, core_rbac, ANALYST, "user-1")
        rid = _intake(client, jwks_env, core_rbac, "my-requests")
        assert _first_channel(client, tok, rid) == "my_requests"

    def test_engineering_caller_records_engineering_channel(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        tok = _as(jwks_env, core_rbac, ANALYST, "user-1")
        rid = _intake(client, jwks_env, core_rbac, "engineering")
        assert _first_channel(client, tok, rid) == "engineering"

    def test_absent_caller_keeps_legacy_portal_channel(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        tok = _as(jwks_env, core_rbac, ANALYST, "user-1")
        rid = _intake(client, jwks_env, core_rbac, None)
        assert _first_channel(client, tok, rid) == "portal"

    def test_unknown_caller_falls_back_to_portal(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        tok = _as(jwks_env, core_rbac, ANALYST, "user-1")
        rid = _intake(client, jwks_env, core_rbac, "some-future-app")
        assert _first_channel(client, tok, rid) == "portal"


class TestParticipantsBff:
    def test_lookup_requires_engineering_access(
        self, client, jwks_env, core_rbac
    ):
        tok = _as(jwks_env, core_rbac, ["other.access"], "user-9")
        resp = _post(
            client, "/v1/participants/lookup", tok, json={"ids": ["u-1"]}
        )
        assert resp.status_code == 403, resp.text

    def test_lookup_returns_items_envelope(
        self, client, jwks_env, core_rbac
    ):
        tok = _as(jwks_env, core_rbac, ANALYST, "user-9")
        resp = _post(
            client, "/v1/participants/lookup", tok, json={"ids": ["u-1"]}
        )
        assert resp.status_code == 200, resp.text
        items = resp.json()["data"]["items"]
        assert items == [{"user_id": "u-1", "has_photo": False}]

    def test_avatar_missing_photo_is_404_not_500(
        self, client, jwks_env, core_rbac
    ):
        """Sem foto na Core → 404 honesto (MFE cai em iniciais)."""
        tok = _as(jwks_env, core_rbac, ANALYST, "user-9")
        resp = _get(client, "/v1/participants/u-1/avatar", tok)
        assert resp.status_code == 404, resp.text
