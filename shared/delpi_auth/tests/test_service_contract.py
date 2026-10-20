from __future__ import annotations

import pytest

from delpi_auth.service_contract import (
    SERVICE_AUTHORIZATION_HEADER,
    build_service_authorization,
    extract_service_authorization,
)


def test_build_service_authorization_adds_bearer_prefix():
    assert build_service_authorization("jwt-value") == "Bearer jwt-value"


def test_build_service_authorization_rejects_empty_token():
    with pytest.raises(ValueError):
        build_service_authorization("  ")


def test_extract_returns_none_when_header_absent():
    assert extract_service_authorization({"Authorization": "Bearer user"}) is None
    assert extract_service_authorization(None) is None
    assert extract_service_authorization({}) is None


def test_extract_is_case_insensitive_and_returns_raw_token():
    headers = {SERVICE_AUTHORIZATION_HEADER.lower(): "Bearer service-jwt"}
    assert extract_service_authorization(headers) == "service-jwt"


def test_extract_rejects_non_bearer_scheme():
    with pytest.raises(ValueError, match="Bearer"):
        extract_service_authorization({SERVICE_AUTHORIZATION_HEADER: "opaque-secret"})


def test_extract_rejects_empty_bearer_value():
    with pytest.raises(ValueError):
        extract_service_authorization({SERVICE_AUTHORIZATION_HEADER: "Bearer "})


def test_extract_rejects_blank_header():
    assert extract_service_authorization({SERVICE_AUTHORIZATION_HEADER: "   "}) is None
