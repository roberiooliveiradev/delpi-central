# shared/delpi_auth/tests/test_cors_policy.py
"""Tests for the canonical CORS origin policy (SEC-CORS-01)."""

from delpi_auth.cors_policy import (
    LOCALHOST_ORIGIN,
    build_allowed_origins,
    normalize_origin,
)


def test_explicit_origins_from_public_base_and_keycloak_urls():
    origins = build_allowed_origins(
        public_base_url="https://minhadelpi.com.br/",
        keycloak_url="https://minhadelpi.com.br/auth",
        environment="production",
        environ={},
    )
    assert origins == ["https://minhadelpi.com.br"]


def test_keycloak_url_without_auth_suffix_is_normalized():
    origins = build_allowed_origins(
        public_base_url=None,
        keycloak_url="https://sso.example.com/",
        environment="production",
        environ={},
    )
    assert origins == ["https://sso.example.com"]


def test_localhost_added_only_outside_production():
    dev = build_allowed_origins(
        public_base_url="https://app.example.com",
        environment="development",
        environ={},
    )
    prod = build_allowed_origins(
        public_base_url="https://app.example.com",
        environment="production",
        environ={},
    )
    assert LOCALHOST_ORIGIN in dev
    assert LOCALHOST_ORIGIN not in prod


def test_empty_configuration_never_returns_wildcard():
    origins = build_allowed_origins(
        public_base_url=None,
        keycloak_url=None,
        environment="production",
        environ={},
    )
    assert origins == []
    assert "*" not in origins


def test_wildcard_extra_origin_is_rejected():
    origins = build_allowed_origins(
        public_base_url="https://app.example.com",
        extra_origins=("*",),
        environment="production",
        environ={},
    )
    assert "*" not in origins
    assert origins == ["https://app.example.com"]


def test_malformed_origins_are_dropped():
    assert normalize_origin("not-a-url") is None
    assert normalize_origin("javascript:alert(1)") is None
    assert normalize_origin("ftp://files.example.com") is None
    assert normalize_origin("") is None
    assert normalize_origin(None) is None
    assert normalize_origin("  ") is None


def test_extra_origins_are_included_and_normalized():
    origins = build_allowed_origins(
        public_base_url="https://app.example.com",
        extra_origins=("https://chatgpt.com/",),
        environment="production",
        environ={},
    )
    assert "https://chatgpt.com" in origins


def test_environment_falls_back_to_api_delpi_env():
    env = {"API_DELPI_ENV": "production", "PUBLIC_BASE_URL": "https://app.example.com"}
    origins = build_allowed_origins(environ=env)
    assert LOCALHOST_ORIGIN not in origins
    assert origins == ["https://app.example.com"]


def test_origins_fall_back_to_env_vars():
    env = {
        "API_DELPI_ENV": "production",
        "PUBLIC_BASE_URL": "https://app.example.com",
        "VITE_KC_URL": "https://app.example.com/auth",
    }
    origins = build_allowed_origins(environ=env)
    assert origins == ["https://app.example.com"]


def test_origins_are_sorted_and_deduplicated():
    origins = build_allowed_origins(
        public_base_url="https://b.example.com",
        keycloak_url="https://a.example.com/auth",
        extra_origins=("https://b.example.com",),
        environment="production",
        environ={},
    )
    assert origins == ["https://a.example.com", "https://b.example.com"]
