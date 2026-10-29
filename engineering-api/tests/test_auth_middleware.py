"""Fluxo real de autenticação/autorização no harness isolado.

A rota /probe existe apenas dentro do app de teste — nunca registrada no
app produtivo, no OpenAPI de produção ou no gateway. O mecanismo exercitado
(jwt_middleware + require_any_permission + resolve_user_context) é o mesmo
das rotas de negócio futuras.
"""

import time

import httpx
import pytest
from jose import jwt

from conftest import rbac_payload


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- positive / negative de autorização efetiva ---


def test_authenticated_with_permission_grants(jwks_env, core_rbac, probe_client):
    token = jwks_env["make_token"]()
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 200
    assert response.json() == {"status": "granted"}


def test_authenticated_without_permission_forbidden(jwks_env, core_rbac, probe_client):
    core_rbac["behavior"] = ("data", rbac_payload([]))
    token = jwks_env["make_token"]()
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 403


def test_sibling_app_permission_does_not_grant(jwks_env, core_rbac, probe_client):
    core_rbac["behavior"] = (
        "data",
        rbac_payload(["dashboard-engineering.view", "dashboard-lmps.view"]),
    )
    token = jwks_env["make_token"]()
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 403


def test_jwt_claims_never_grant_access(jwks_env, core_rbac, probe_client):
    """Permissions/is_superadmin dentro do JWT não são autoridade."""
    core_rbac["behavior"] = ("data", rbac_payload([]))
    token = jwks_env["make_token"](
        permissions=["engineering.access"],
        is_superadmin=True,
        realm_access={"roles": ["superadmin"]},
    )
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 403


def test_superadmin_from_core_grants(jwks_env, core_rbac, probe_client):
    """is_superadmin efetivo vem da Core, não do token."""
    core_rbac["behavior"] = (
        "data",
        rbac_payload([], is_superadmin=True),
    )
    token = jwks_env["make_token"]()
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 200


# --- falhas de autenticação ---


def test_missing_authorization_header_unauthorized(probe_client):
    response = probe_client.get("/probe")
    assert response.status_code == 401


def test_malformed_authorization_header_unauthorized(probe_client):
    assert probe_client.get("/probe", headers={"Authorization": "Token abc"}).status_code == 401
    assert probe_client.get("/probe", headers={"Authorization": "Bearer"}).status_code == 401
    assert probe_client.get("/probe", headers=_auth("not-a-jwt")).status_code == 401


def test_expired_token_unauthorized(jwks_env, core_rbac, probe_client):
    now = int(time.time())
    token = jwks_env["make_token"](iat=now - 600, exp=now - 300)
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 401


def test_wrong_signature_unauthorized(jwks_env, core_rbac, probe_client):
    token = jwks_env["make_wrong_key_token"]()
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 401


def test_wrong_issuer_unauthorized(jwks_env, core_rbac, probe_client):
    token = jwks_env["make_token"](iss="https://evil.test/realms/fake")
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 401


def test_wrong_audience_unauthorized(jwks_env, core_rbac, probe_client):
    token = jwks_env["make_token"](aud="other-audience")
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 401


def test_missing_required_claims_unauthorized(jwks_env, core_rbac, probe_client):
    token = jwks_env["make_token"](email=None)
    assert probe_client.get("/probe", headers=_auth(token)).status_code == 401
    token = jwks_env["make_token"](sub=None)
    assert probe_client.get("/probe", headers=_auth(token)).status_code == 401


# --- autoridade indisponível: fail-closed ---


def test_core_unavailable_denies_access(jwks_env, core_rbac, probe_client):
    core_rbac["behavior"] = ("raise", httpx.TimeoutException("core timeout"))
    token = jwks_env["make_token"]()
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 503


def test_core_error_denies_access(jwks_env, core_rbac, probe_client):
    core_rbac["behavior"] = (
        "raise",
        RuntimeError("RBAC lookup failed with status 500"),
    )
    token = jwks_env["make_token"]()
    response = probe_client.get("/probe", headers=_auth(token))
    assert response.status_code == 503


# --- superfície pública e isolamento ---


@pytest.mark.parametrize("path", ["/health", "/ready", "/openapi.json"])
def test_public_paths_do_not_require_token(client, path):
    response = client.get(path)
    assert response.status_code != 401


@pytest.mark.parametrize(
    "path",
    [
        "/apps/engineering-api/health",
        "/apps/engineering-api/ready",
    ],
)
def test_root_path_public_variants(client, path):
    """Variantes canônicas de root_path dispensam JWT (rota → 404, não 401).

    O gateway faz strip do prefixo; acesso direto ao path prefixado é 404,
    mas o middleware não pode exigir Bearer — contrato aprovado F1.S2.
    """
    response = client.get(path)
    assert response.status_code != 401


def test_non_public_path_requires_token(client):
    response = client.get("/v1/anything")
    assert response.status_code == 401


# --- F1.S2R1 — allowlist estrita: nenhum prefixo arbitrário dispensa JWT ---


@pytest.mark.parametrize(
    "path",
    [
        "/qualquer-prefixo/engineering-api/health",
        "/qualquer-prefixo/engineering-api/ready",
        "/fake/apps/engineering-api/health",
        "/fake/apps/engineering-api/ready",
        "/v1/home",
        "/v1/health",
        "/v1/ready",
        "/engineering-api/health",           # sem o prefixo /apps canônico
        "/engineering-api/ready",
        "/engineering-api/health/extra",
        "/apps/engineering-api/health/extra",
        "/apps/engineering-api/ready/extra",
        "/xapps/engineering-api/health",     # prefixo parecido
        "/appsx/engineering-api/health",
        "/apps/engineering-apix/health",
        "//health",                          # dupla barra
        "/apps//engineering-api/health",
        "/nonexistent-route",
        # política pública da lib é mais ampla que o contrato da
        # Engenharia — estes paths NÃO podem dispensar JWT:
        "/foo/docs",
        "/x/redoc",
        "/x/openapi.json",
        "/apps/commercial-api/health",       # health de outro serviço
        "/x/api-delpi/health",
    ],
)
def test_arbitrary_prefixes_require_auth(client, path):
    response = client.get(path)
    assert response.status_code == 401


@pytest.mark.parametrize(
    "path",
    [
        "/health/",
        "/ready/",
        "/apps/engineering-api/health/",
    ],
)
def test_trailing_slash_public_but_not_found(client, path):
    """Trailing slash normaliza para a rota pública (redirect_slashes=False
    → 404, nunca 401)."""
    response = client.get(path)
    assert response.status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/./health",
        "/x/../health",
        "/x/./../health",
    ],
)
def test_dot_segments_resolve_to_canonical_route(client, path):
    """O client/transporte normaliza segmentos . e .. ANTES do middleware —
    a requisição chega como /health (rota pública legítima, não bypass)."""
    response = client.get(path)
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_encoded_path_matches_exact_route(client):
    """%61 decodifica para 'a' — /he%61lth é o próprio /health."""
    response = client.get("/he%61lth")
    assert response.status_code != 401


def test_query_string_does_not_affect_matching(client):
    assert client.get("/health?foo=bar").status_code == 200
    response = client.get("/v1/anything?x=/health")
    assert response.status_code == 401


def test_allowlist_matches_only_exact_paths():
    """Unit check da classificação — normalize_path + comparação exata."""
    from engineering_app.middleware.auth_middleware import (
        _is_engineering_public_path,
    )

    public = {
        "/health",
        "/ready",
        "/apps/engineering-api/health",
        "/apps/engineering-api/ready",
        "/openapi.json",
        "/docs",
        "/redoc",
        "/apps/engineering-api/openapi.json",
        "/apps/engineering-api/docs",
        "/apps/engineering-api/redoc",
    }
    for path in public:
        assert _is_engineering_public_path(path), path

    forbidden = [
        "/x/engineering-api/health",
        "/engineering-api/health",
        "/apps/engineering-api/health/extra",
        "/v1/health",
        "/foo/openapi.json",
        "/x/docs",
        "",
        "/",
    ]
    for path in forbidden:
        assert not _is_engineering_public_path(path), path


def test_probe_route_not_in_production_openapi(client):
    spec = client.get("/openapi.json").json()
    assert "/probe" not in spec["paths"]
    assert "/probe/whoami" not in spec["paths"]
    assert set(spec["paths"].keys()) == {
        "/health",
        "/ready",
        "/v1/home",
        "/v1/overview",
        "/v1/lmps",
        "/v1/lmps/summary",
        "/v1/lmps/goal-context",
        "/v1/lmps/department-idd",
        "/v1/lmps/nonconformities/streak",
        "/v1/lmps/{sale_number}",
        "/v1/lmps/{sale_number}/history/events",
        "/v1/lmps/{sale_number}/history/flow",
        "/v1/products/{product_code}/structure",
        "/public/characters/{character_id}/avatar/{filename}",
        "/v1/nonconformities",
        "/v1/nonconformities/{record_id}",
        "/v1/nonconformities/{record_id}/history",
        "/v1/nonconformities/{record_id}/context",
        "/v1/nonconformities/indicators",
        "/v1/nonconformities/problem-tags",
        "/v1/nonconformities/export",
        "/v1/nonconformities/import",
        "/v1/nonconformities/prepare",
    }


def test_service_token_headers_do_not_bypass(jwks_env, core_rbac, probe_client, monkeypatch):
    """Token de serviço interno não substitui identidade de usuário."""
    monkeypatch.delenv("API_DELPI_INTERNAL_SERVICE_TOKEN", raising=False)
    token = jwks_env["make_token"]()
    response = probe_client.get(
        "/probe",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Delpi-Service-Token": "fake-internal-token",
        },
    )
    assert response.status_code == 200  # via JWT válido, não via service token

    response = probe_client.get(
        "/probe",
        headers={
            "Authorization": "Bearer fake-internal-token",
            "X-Delpi-Service-Token": "fake-internal-token",
        },
    )
    assert response.status_code == 401


def test_service_token_mints_service_principal_when_configured(probe_client, monkeypatch):
    """Comportamento canônico do delpi_auth: service token válido cria
    principal ``service`` superadmin (server-to-server). Rotas futuras de
    dados de usuário devem exigir ``principal_type == "user"`` — não é
    autorização de usuário, é o mecanismo oficial de integração interna.
    """
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-token-for-test-only")
    response = probe_client.get(
        "/probe/whoami",
        headers={"X-Delpi-Service-Token": "svc-token-for-test-only"},
    )
    assert response.status_code == 200
    assert response.json()["principal_type"] == "service"


def test_user_context_does_not_leak_between_requests(jwks_env, core_rbac, probe_client):
    def _rbac_for(token):
        claims = jwt.get_unverified_claims(token)
        return rbac_payload(
            ["engineering.access"], email=claims["email"], id=claims["sub"]
        )

    core_rbac["behavior"] = ("fn", _rbac_for)
    token_a = jwks_env["make_token"](email="a@delpi.test", sub="user-a")
    token_b = jwks_env["make_token"](email="b@delpi.test", sub="user-b")

    resp_a = probe_client.get("/probe/whoami", headers=_auth(token_a))
    assert resp_a.status_code == 200
    assert resp_a.json()["email"] == "a@delpi.test"

    unauth = probe_client.get("/probe/whoami")
    assert unauth.status_code == 401

    resp_b = probe_client.get("/probe/whoami", headers=_auth(token_b))
    assert resp_b.status_code == 200
    assert resp_b.json()["email"] == "b@delpi.test"


# --- EVA.MCP.V1.R1 — metadata OAuth: allowlist exata (sem substring) ---


@pytest.mark.parametrize(
    "path",
    [
        # rotas oficiais registradas (MCP_RESOURCE_CONFIG.metadata_paths)
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/mcp",
        # variantes prefixadas (root_path/gateway)
        "/apps/engineering-api/.well-known/oauth-protected-resource",
        "/apps/engineering-api/.well-known/oauth-protected-resource/mcp",
    ],
)
def test_oauth_metadata_exact_paths_are_public(client, path):
    """Metadata RFC 9728 dispensa JWT nos caminhos exatos registrados."""
    response = client.get(path)
    assert response.status_code != 401


@pytest.mark.parametrize(
    "path",
    [
        # prefixos arbitrários
        "/fake/.well-known/oauth-protected-resource",
        "/v1/.well-known/oauth-protected-resource",
        "/x/apps/engineering-api/.well-known/oauth-protected-resource",
        "/apps/fake/.well-known/oauth-protected-resource",
        "/fake/.well-known/oauth-protected-resource/mcp",
        "/x/apps/engineering-api/.well-known/oauth-protected-resource/mcp",
        # sufixos arbitrários
        "/.well-known/oauth-protected-resource/extra",
        "/.well-known/oauth-protected-resource-fake",
        "/.well-known/oauth-protected-resourceXYZ",
        "/apps/engineering-api/.well-known/oauth-protected-resource/extra",
        "/apps/engineering-api/.well-known/oauth-protected-resource-fake",
        "/.well-known/oauth-protected-resource/mcp/extra",
        "/.well-known/oauth-protected-resource/mcpX",
        # substring em outros segmentos
        "/foo/.well-known/oauth-protected-resource/bar",
        "/api/.well-known/oauth-protected-resource/debug",
        "/v1/test/.well-known/oauth-protected-resource",
        # segmentos pais do bem-known não são wildcard
        "/.well-known",
        "/.well-known/other",
        "/.well-known/openid-configuration",
    ],
)
def test_oauth_metadata_arbitrary_paths_require_auth(client, path):
    """Qualquer path que apenas contenha a substring de metadata exige JWT —
    401 antes do roteamento, nunca 404."""
    response = client.get(path)
    assert response.status_code == 401


def test_oauth_metadata_allowlist_exact_matching():
    """Unit check — o predicado não usa substring nem prefixo."""
    from engineering_app.middleware.auth_middleware import (
        _is_engineering_public_path,
        _PUBLIC_OAUTH_METADATA_PATHS,
    )

    public = {
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/mcp",
        "/apps/engineering-api/.well-known/oauth-protected-resource",
        "/apps/engineering-api/.well-known/oauth-protected-resource/mcp",
        # trailing slash normaliza para o caminho canônico
        "/.well-known/oauth-protected-resource/",
        "/apps/engineering-api/.well-known/oauth-protected-resource/",
        # query string é ignorada pela normalização
        "/.well-known/oauth-protected-resource?x=1",
    }
    for path in public:
        assert _is_engineering_public_path(path), path

    forbidden = [
        "/fake/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/extra",
        "/.well-known/oauth-protected-resource-fake",
        "/.well-known/oauth-protected-resourceXYZ",
        "/apps/engineering-api/.well-known/oauth-protected-resource/extra",
        "/foo/.well-known/oauth-protected-resource/bar",
        "/v1/.well-known/oauth-protected-resource",
        "/x/apps/engineering-api/.well-known/oauth-protected-resource",
        "/apps/fake/.well-known/oauth-protected-resource",
        "/.well-known",
        "//.well-known/oauth-protected-resource",  # dupla barra ≠ canonical
        "/.well-known//oauth-protected-resource",
    ]
    for path in forbidden:
        assert not _is_engineering_public_path(path), path

    # a allowlist é derivada das rotas registradas — nada além delas
    assert _PUBLIC_OAUTH_METADATA_PATHS == {
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/mcp",
        "/apps/engineering-api/.well-known/oauth-protected-resource",
        "/apps/engineering-api/.well-known/oauth-protected-resource/mcp",
    }
