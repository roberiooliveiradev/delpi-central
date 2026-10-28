"""F1.S4 — consolidação de segurança e observabilidade.

Cobre: allowlist sem mutação de scope, logging por template de rota,
respostas 500 instrumentadas, concorrência real (AsyncClient + gather)
e distinção user/service principal.
"""

import asyncio
import logging
import re

import httpx
import pytest
from jose import jwt as jose_jwt

from delpi_auth.service_token import apply_internal_service_headers

from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

from conftest import ENGINEERING_ACCESS, rbac_payload

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_REQUEST_LOGGER = "engineering_api.request"


def _request_id_of(response) -> str:
    return response.headers.get("X-Request-Id", "")


# --- allowlist sem mutação de scope ---


def test_auth_middleware_does_not_mutate_scope_path(client):
    """F1.S4: residual S2R1 resolvido — nenhum masking de scope[path]."""
    response = client.get("/x/api-delpi/health")
    assert response.status_code == 401  # auth exigida sem tocar o path


@pytest.mark.parametrize(
    "path",
    [
        "/qualquer-prefixo/engineering-api/health",
        "/fake/apps/engineering-api/ready",
        "/foo/docs",
        "/x/openapi.json",
        "/apps/commercial-api/health",
        "/v1/health",
    ],
)
def test_broad_policy_paths_still_require_auth(client, path):
    assert client.get(path).status_code == 401


# --- logging por template de rota ---


def test_parameterized_route_logs_template_not_identifier(
    probe_client, jwks_env, core_rbac, caplog
):
    """Path real nunca vaza: log carrega o template da rota."""
    token = jwks_env["make_token"]()
    with caplog.at_level(logging.INFO, logger=_REQUEST_LOGGER):
        response = probe_client.get(
            "/probe/items/dwg-SECRET-777",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    record = next(
        r for r in caplog.records if "engineering_api_request" in r.message
    )
    msg = record.getMessage()
    assert "path=/probe/items/{item_id}" in msg
    assert "dwg-SECRET-777" not in msg


# --- respostas 500 instrumentadas ---


def test_unhandled_exception_on_public_route_is_instrumented(
    probe_client, caplog
):
    """500 fora do boundary de auth: headers + envelope canônico."""
    with caplog.at_level(logging.ERROR, logger=_REQUEST_LOGGER):
        response = probe_client.get("/health")
    assert response.status_code == 500
    assert _UUID_RE.match(_request_id_of(response))
    assert float(response.headers["X-Response-Time-Ms"]) >= 0
    assert response.headers["X-Operation-Id"] == "test_public_boom"

    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Erro interno do servidor."
    assert "public-boom-internal" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text

    record = next(
        r
        for r in caplog.records
        if "engineering_api_request" in r.message and "error_class" in r.message
    )
    assert "status=500" in record.getMessage()
    assert "error_class=RuntimeError" in record.getMessage()


def test_unhandled_exception_on_authenticated_route_is_instrumented(
    probe_client, jwks_env, core_rbac
):
    """500 dentro do boundary de auth (delpi_auth): headers preservados."""
    token = jwks_env["make_token"]()
    response = probe_client.get(
        "/probe/boom", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 500
    assert _UUID_RE.match(_request_id_of(response))
    assert float(response.headers["X-Response-Time-Ms"]) >= 0
    assert response.headers["X-Operation-Id"] == "test_engineering_boom"
    # Contrato canônico delpi_auth para erros dentro do seu boundary.
    assert response.json()["detail"] == "Internal server error"
    assert "sensitive-boom-internal" not in response.text


def test_context_reset_after_exception(probe_client, jwks_env, core_rbac):
    token = jwks_env["make_token"]()
    response = probe_client.get(
        "/probe/boom", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 500
    assert get_request_id() is None


# --- service principal nunca é confundido com usuário ---


def test_service_principal_marked_and_not_confused_with_user(
    probe_client, monkeypatch, jwks_env
):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-token-42")
    headers = {}
    apply_internal_service_headers(headers)
    response = probe_client.get("/probe/whoami", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["principal_type"] == "service"
    # Não carrega email de usuário humano.
    assert body["email"] == "service@delpi.internal"


def test_arbitrary_service_header_does_not_bypass_auth(probe_client):
    response = probe_client.get(
        "/probe/whoami", headers={"X-Delpi-Service-Token": "wrong-token"}
    )
    assert response.status_code == 401


# --- concorrência real ---


def _rbac_from_token_claims(token: str) -> dict:
    claims = jose_jwt.get_unverified_claims(token)
    return rbac_payload(
        [ENGINEERING_ACCESS], id=claims["sub"], email=claims["email"]
    )


async def test_concurrent_requests_isolate_request_id_and_user(
    probe_asgi_app, jwks_env, core_rbac
):
    """Requests assíncronas sobrepostas: ids e contextos não se misturam."""
    core_rbac["behavior"] = ("fn", _rbac_from_token_claims)
    token_a = jwks_env["make_token"](sub="user-a", email="a@delpi.test")
    token_b = jwks_env["make_token"](sub="user-b", email="b@delpi.test")

    transport = httpx.ASGITransport(app=probe_asgi_app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", timeout=10.0
    ) as client:
        responses = await asyncio.gather(
            *[
                client.get(
                    "/probe/context",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-Request-Id": rid,
                    },
                )
                for token, rid in [
                    (token_a, "conc-a-1"),
                    (token_b, "conc-b-1"),
                    (token_a, "conc-a-2"),
                    (token_b, "conc-b-2"),
                    (token_a, "conc-a-3"),
                    (token_b, "conc-b-3"),
                ]
            ]
        )

    expected_email = {"conc-a": "a@delpi.test", "conc-b": "b@delpi.test"}
    for response in responses:
        assert response.status_code == 200
        rid = response.headers["X-Request-Id"]
        body = response.json()
        assert body["request_id"] == rid
        assert body["email"] == expected_email[rid.rsplit("-", 1)[0]]
        assert body["principal_type"] == "user"

    # Contexto limpo após o lote — sem vazamento para o caller.
    assert get_request_id() is None


async def test_concurrent_failure_does_not_poison_siblings(
    probe_asgi_app, jwks_env, core_rbac
):
    """Uma request falhando em paralelo não contamina a irmã saudável."""
    core_rbac["behavior"] = ("fn", _rbac_from_token_claims)
    token_a = jwks_env["make_token"](sub="user-a", email="a@delpi.test")
    token_b = jwks_env["make_token"](sub="user-b", email="b@delpi.test")

    transport = httpx.ASGITransport(app=probe_asgi_app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", timeout=10.0
    ) as client:
        ok, denied = await asyncio.gather(
            client.get(
                "/probe/context",
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "X-Request-Id": "sib-ok",
                },
            ),
            client.get(
                "/probe/context",
                headers={"X-Request-Id": "sib-denied"},
            ),
        )

    assert ok.status_code == 200
    assert ok.json()["request_id"] == "sib-ok"
    assert denied.status_code == 401
    assert denied.headers["X-Request-Id"] == "sib-denied"
    assert get_request_id() is None
