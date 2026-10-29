"""G4.A.R1 — autenticação interserviços do adapter facts LMP.

Verifica o boundary corrigido: a credencial técnica viaja em
`X-Delpi-Service-Authorization` (S2S individual Keycloak), o Bearer
humano permanece como ator delegado, o token legado compartilhado nunca
é emitido e a ausência de credencial falha fechado (`unavailable`)
ANTES de qualquer chamada HTTP.
"""

from __future__ import annotations

import httpx
import pytest

from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceTokenRequestError,
)
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.infrastructure.gateways.api_delpi_facts import (
    ApiDelpiFactsSource,
)
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
)

CTX = HomeSourceContext(
    user_id="user-1", access_token="user-jwt-1", request_id="req-1"
)


def _facts_payload(items=(), total=0):
    return {
        "success": True,
        "data": {
            "items": list(items),
            "total": total,
            "page": 1,
            "page_size": 50,
            "total_pages": 0,
            "provenance": {"source_system": "TOTVS"},
            "policy": {},
        },
    }


def _source(handler, token_getter=lambda: "svc-jwt-1"):
    return ApiDelpiFactsSource(
        DownstreamClient(
            "http://delpi-api-delpi:8000",
            timeout_seconds=2.0,
            transport=httpx.MockTransport(handler),
        ),
        token_getter,
    )


async def test_facts_sends_s2s_header_and_keeps_delegated_human_bearer():
    """Boundary G4.A.R1: identidade técnica + ator delegado, separados."""
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=_facts_payload())

    result = await _source(handler).fetch_facts(
        CTX,
        start_date=None,
        end_date=None,
        branch=None,
        listing_type="LMP",
        page=1,
        page_size=50,
        include_qtd_pi=False,
    )

    assert result.status == "empty"
    request = captured[0]
    assert (
        request.headers["x-delpi-service-authorization"]
        == "Bearer svc-jwt-1"
    )
    assert request.headers["authorization"] == "Bearer user-jwt-1"
    assert request.headers["x-delpi-caller-app"] == "engineering-api"
    assert request.headers["x-request-id"] == "req-1"
    # Token legado compartilhado nunca é emitido (G4.A.R1/F2a.R1).
    assert "x-delpi-service-token" not in request.headers


async def test_pi_counts_sends_s2s_header_on_post():
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "items": [
                        {"branch": "01", "sale_number": "OV900",
                         "revision": "001", "qtd_pi": 5}
                    ],
                    "provenance": {},
                },
            },
        )

    result = await _source(handler).fetch_pi_counts(
        CTX,
        ov_keys=[{"branch": "01", "sale_number": "OV900", "revision": "001"}],
        branch=None,
    )

    assert result.status == "available"
    request = captured[0]
    assert (
        request.headers["x-delpi-service-authorization"]
        == "Bearer svc-jwt-1"
    )
    assert request.headers["authorization"] == "Bearer user-jwt-1"
    assert "x-delpi-service-token" not in request.headers


async def test_facts_unavailable_when_s2s_config_missing_no_http_call():
    """Fail-closed: sem credencial S2S configurada, nenhuma chamada sai."""
    called = []

    def handler(request: httpx.Request) -> httpx.Response:
        called.append(request)
        return httpx.Response(200, json=_facts_payload())

    def broken_getter() -> str:
        raise ServiceAuthConfigError("Missing S2S provider configuration")

    result = await _source(handler, broken_getter).fetch_facts(
        CTX,
        start_date=None,
        end_date=None,
        branch=None,
        listing_type="LMP",
        page=1,
        page_size=50,
        include_qtd_pi=False,
    )

    assert result.status == "unavailable"
    assert result.reason == "service_auth_unavailable"
    assert called == []  # nenhum HTTP emitido sem credencial válida


async def test_facts_unavailable_when_s2s_token_request_fails():
    """Emissor indisponível/rejeitando grant → unavailable, sem fallback."""
    called = []

    def handler(request: httpx.Request) -> httpx.Response:
        called.append(request)
        return httpx.Response(200, json=_facts_payload())

    def broken_getter() -> str:
        raise ServiceTokenRequestError("S2S token endpoint rejected the grant")

    result = await _source(handler, broken_getter).fetch_pi_counts(
        CTX, ov_keys=[{"branch": "01", "sale_number": "1", "revision": "1"}],
        branch=None,
    )

    assert result.status == "unavailable"
    assert result.reason == "service_auth_unavailable"
    assert called == []


async def test_facts_s2s_denied_by_api_delpi_maps_forbidden():
    """api-delpi negando a credencial técnica → forbidden honesto."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "success": False,
                "error": {"code": "S2S_SCOPE_DENIED", "message": "Forbidden"},
            },
        )

    result = await _source(handler).fetch_facts(
        CTX,
        start_date=None,
        end_date=None,
        branch=None,
        listing_type="LMP",
        page=1,
        page_size=50,
        include_qtd_pi=False,
    )

    assert result.status == "forbidden"


async def test_facts_missing_service_token_header_denied_by_api_delpi():
    """Sem o header S2S a api-delpi nega (401) — o adapter reporta
    forbidden, nunca sucesso silencioso."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "success": False,
                "error": {
                    "code": "S2S_TOKEN_MISSING",
                    "message": "Service authentication required",
                },
            },
        )

    result = await _source(handler, lambda: "").fetch_facts(
        CTX,
        start_date=None,
        end_date=None,
        branch=None,
        listing_type="LMP",
        page=1,
        page_size=50,
        include_qtd_pi=False,
    )

    assert result.status == "forbidden"
