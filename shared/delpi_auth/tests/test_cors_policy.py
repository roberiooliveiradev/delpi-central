# shared/delpi_auth/tests/test_cors_policy.py
"""Tests for the canonical CORS origin policy (SEC-CORS-01).

All tests control the environment explicitly via the ``environ`` mapping
or the ``environment`` argument — no test relies on ambient os.environ.
"""

from delpi_auth.cors_policy import (
    LOCALHOST_ORIGIN,
    build_allowed_origins,
    normalize_origin,
)

# ------------------------------------------------------------------
# normalize_origin — accepted shapes
# ------------------------------------------------------------------


def test_normalize_origin_accepts_bare_origin():
    assert normalize_origin("https://app.example.com") == "https://app.example.com"


def test_normalize_origin_strips_single_trailing_slash():
    assert normalize_origin("https://app.example.com/") == "https://app.example.com"


def test_normalize_origin_normalizes_case():
    assert normalize_origin("HTTPS://APP.EXAMPLE.COM/") == "https://app.example.com"


def test_normalize_origin_preserves_explicit_port():
    assert normalize_origin("http://localhost:5173") == "http://localhost:5173"
    assert normalize_origin("https://app.example.com:8443") == "https://app.example.com:8443"


def test_normalize_origin_accepts_ipv6_literal():
    assert normalize_origin("http://[::1]:8080") == "http://[::1]:8080"


# ------------------------------------------------------------------
# normalize_origin — strict rejection (negative + boundary)
# ------------------------------------------------------------------


def test_normalize_origin_rejects_empty_and_wildcard():
    assert normalize_origin("") is None
    assert normalize_origin(None) is None
    assert normalize_origin("  ") is None
    assert normalize_origin("*") is None


def test_normalize_origin_rejects_paths():
    assert normalize_origin("https://app.example.com/path") is None
    assert normalize_origin("https://app.example.com/path/") is None
    assert normalize_origin("https://app.example.com//") is None
    assert normalize_origin("https://app.example.com/auth/realms/x") is None


def test_normalize_origin_rejects_query_and_fragment():
    assert normalize_origin("https://app.example.com?x=1") is None
    assert normalize_origin("https://app.example.com/#frag") is None


def test_normalize_origin_rejects_embedded_credentials():
    assert normalize_origin("https://user:pass@app.example.com") is None
    assert normalize_origin("https://user@app.example.com") is None


def test_normalize_origin_rejects_malformed_authority():
    assert normalize_origin("not-a-url") is None
    assert normalize_origin("//app.example.com") is None
    assert normalize_origin("http://") is None
    assert normalize_origin("https://:8080") is None
    assert normalize_origin("https://app.example.com:abc") is None
    assert normalize_origin("https://app.example.com:99999") is None
    assert normalize_origin("https://app exam ple.com") is None


def test_normalize_origin_rejects_non_http_schemes():
    assert normalize_origin("ftp://files.example.com") is None
    assert normalize_origin("javascript:alert(1)") is None
    assert normalize_origin("file:///etc/passwd") is None


def test_normalize_origin_rejects_wildcard_hosts():
    assert normalize_origin("https://*") is None
    assert normalize_origin("https://*.example.com") is None


# ------------------------------------------------------------------
# build_allowed_origins — origins
# ------------------------------------------------------------------


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


def test_keycloak_url_with_foreign_path_is_rejected():
    origins = build_allowed_origins(
        public_base_url=None,
        keycloak_url="https://sso.example.com/realms/delpi",
        environment="production",
        environ={},
    )
    assert origins == []


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


def test_invalid_public_base_url_is_rejected_not_repaired():
    origins = build_allowed_origins(
        public_base_url="https://app.example.com/admin?debug=1",
        environment="production",
        environ={},
    )
    assert origins == []


def test_extra_origins_are_included_and_normalized():
    origins = build_allowed_origins(
        public_base_url="https://app.example.com",
        extra_origins=("https://chatgpt.com/",),
        environment="production",
        environ={},
    )
    assert "https://chatgpt.com" in origins


def test_malformed_extra_origin_dropped_siblings_kept():
    origins = build_allowed_origins(
        public_base_url="https://app.example.com",
        extra_origins=("https://chatgpt.com", "https://evil.com/x?y"),
        environment="production",
        environ={},
    )
    assert origins == ["https://app.example.com", "https://chatgpt.com"]


def test_origins_are_sorted_and_deduplicated():
    origins = build_allowed_origins(
        public_base_url="https://b.example.com",
        keycloak_url="https://a.example.com/auth",
        extra_origins=("https://b.example.com",),
        environment="production",
        environ={},
    )
    assert origins == ["https://a.example.com", "https://b.example.com"]


# ------------------------------------------------------------------
# build_allowed_origins — environment gating (fail-closed)
# ------------------------------------------------------------------


def test_localhost_added_only_in_authorized_local_environments():
    for env_name in ("development", "dev", "local", "test"):
        origins = build_allowed_origins(
            public_base_url="https://app.example.com",
            environment=env_name,
            environ={},
        )
        assert LOCALHOST_ORIGIN in origins, env_name


def test_localhost_never_added_in_production():
    origins = build_allowed_origins(
        public_base_url="https://app.example.com",
        environment="production",
        environ={},
    )
    assert LOCALHOST_ORIGIN not in origins


def test_absent_api_delpi_env_does_not_authorize_localhost():
    origins = build_allowed_origins(
        public_base_url="https://app.example.com",
        environ={},  # API_DELPI_ENV absent
    )
    assert origins == ["https://app.example.com"]
    assert LOCALHOST_ORIGIN not in origins


def test_empty_api_delpi_env_does_not_authorize_localhost():
    origins = build_allowed_origins(
        environ={"API_DELPI_ENV": "", "PUBLIC_BASE_URL": "https://app.example.com"},
    )
    assert LOCALHOST_ORIGIN not in origins


def test_unknown_api_delpi_env_does_not_authorize_localhost():
    for env_name in ("prod", "production2", "staging", "homolog", "qa", "1"):
        origins = build_allowed_origins(
            environ={
                "API_DELPI_ENV": env_name,
                "PUBLIC_BASE_URL": "https://app.example.com",
            },
        )
        assert LOCALHOST_ORIGIN not in origins, env_name
        assert origins == ["https://app.example.com"], env_name


def test_development_api_delpi_env_authorizes_localhost():
    origins = build_allowed_origins(
        environ={
            "API_DELPI_ENV": "development",
            "PUBLIC_BASE_URL": "https://app.example.com",
        },
    )
    assert LOCALHOST_ORIGIN in origins


def test_environment_argument_overrides_env_var():
    origins = build_allowed_origins(
        environ={"API_DELPI_ENV": "development"},
        environment="production",
        public_base_url="https://app.example.com",
    )
    assert LOCALHOST_ORIGIN not in origins


def test_env_var_fallbacks_for_origin_values():
    env = {
        "API_DELPI_ENV": "production",
        "PUBLIC_BASE_URL": "https://app.example.com",
        "VITE_KC_URL": "https://sso.example.com/auth",
    }
    origins = build_allowed_origins(environ=env)
    assert origins == ["https://app.example.com", "https://sso.example.com"]


def test_wildcard_in_env_vars_is_never_inherited():
    origins = build_allowed_origins(
        environ={
            "API_DELPI_ENV": "production",
            "PUBLIC_BASE_URL": "*",
            "VITE_KC_URL": "*",
        },
        extra_origins=("*",),
    )
    assert origins == []
