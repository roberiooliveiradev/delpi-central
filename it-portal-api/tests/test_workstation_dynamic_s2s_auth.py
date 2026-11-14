"""G2-S4-S2a: JWT S2S dinamico nao exige allowlist global de servidores."""
from __future__ import annotations

import uuid

import pytest
from fastapi import Request

import delpi_auth.service_token_validator as validator
from it_portal_app.application.workstation_identity_service import device_client_id
from it_portal_app.config import settings
from it_portal_app.interface.http.s2s_auth import (
    S2SHttpException, require_dynamic_workstation_identity,
)

WID = str(uuid.uuid4())
EXPECTED = device_client_id(WID)


def make_request(token: str | None = "signed-test-token") -> Request:
    headers = []
    if token is not None:
        headers.append((b"x-delpi-service-authorization", f"Bearer {token}".encode()))
    return Request({
        "type": "http", "method": "POST", "path": "/collector/v1/workstations/x/snapshots",
        "headers": headers, "scheme": "https",
    })


def test_dynamic_client_requires_jwt_identity_scope_audience(monkeypatch):
    monkeypatch.setattr(settings, "S2S_AUDIENCE", "it-portal-api")
    monkeypatch.setattr(settings, "S2S_ALLOWED_CLIENTS", "")
    claims = {
        "sub": str(uuid.uuid4()),
        "azp": EXPECTED,
        "aud": "it-portal-api",
        "iss": "https://keycloak.example/realms/delpi",
        "scope": "it-portal.workstations.ingest",
    }
    calls = []
    def signature_verified(token, *, expected_audience):
        calls.append((token, expected_audience))
        return claims
    monkeypatch.setattr(validator, "validate_token", signature_verified)

    identity = require_dynamic_workstation_identity(make_request(), expected_client_id=EXPECTED)
    assert identity.client_id == EXPECTED
    assert calls == [("signed-test-token", "it-portal-api")]
    claims["azp"] = device_client_id(str(uuid.uuid4()))
    with pytest.raises(S2SHttpException) as mismatch:
        require_dynamic_workstation_identity(make_request(), expected_client_id=EXPECTED)
    assert mismatch.value.status_code == 403
    claims["azp"] = EXPECTED
    claims["scope"] = "it-portal.observations.ingest"
    with pytest.raises(S2SHttpException) as missing_scope:
        require_dynamic_workstation_identity(make_request(), expected_client_id=EXPECTED)
    assert missing_scope.value.status_code == 403


def test_dynamic_auth_fails_closed_when_missing_header_or_audience(monkeypatch):
    monkeypatch.setattr(settings, "S2S_AUDIENCE", "it-portal-api")
    with pytest.raises(S2SHttpException) as no_token:
        require_dynamic_workstation_identity(make_request(None), expected_client_id=EXPECTED)
    assert no_token.value.status_code == 401
    monkeypatch.setattr(settings, "S2S_AUDIENCE", "")
    with pytest.raises(S2SHttpException) as no_audience:
        require_dynamic_workstation_identity(make_request(), expected_client_id=EXPECTED)
    assert no_audience.value.status_code == 503
    with pytest.raises(S2SHttpException) as bad_client:
        require_dynamic_workstation_identity(make_request(), expected_client_id="server-admin")
    assert bad_client.value.status_code == 403
