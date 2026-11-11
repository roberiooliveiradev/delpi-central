"""Envio S2S da observação para o it-portal-api."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Mapping

from delpi_auth.service_token_provider import ClientCredentialsTokenProvider

from .diagnose import build_observation_payload

DEFAULT_SCOPE = "it-portal.observations.ingest"
SERVICE_AUTH_HEADER = "X-Delpi-Service-Authorization"
# User-Agent neutro (sem impersonar navegador). Suficiente para gateway local.
DEFAULT_USER_AGENT = "delpi-it-portal-linux-collector/1.0"


def _required_env(name: str, environ: Mapping[str, str]) -> str:
    value = (environ.get(name) or "").strip()
    if not value:
        raise SystemExit(f"Variável obrigatória ausente: {name}")
    return value


def build_ingest_request(
    *,
    base_url: str,
    server_id: str,
    token: str,
    body: dict,
    http_host: str | None = None,
    user_agent: str = DEFAULT_USER_AGENT,
) -> urllib.request.Request:
    """Monta o POST de ingestão — Host customizado só quando explicitamente pedido."""
    url = f"{base_url.rstrip('/')}/collector/v1/servers/{server_id}/observations"
    encoded = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header(SERVICE_AUTH_HEADER, f"Bearer {token}")
    request.add_header("User-Agent", user_agent)
    host = (http_host or "").strip()
    if host:
        request.add_header("Host", host)
    return request


def submit_observation(
    *,
    environ: Mapping[str, str] | None = None,
    payload: dict | None = None,
    http_open=None,
) -> dict:
    env = environ if environ is not None else os.environ
    base_url = _required_env("IT_PORTAL_COLLECTOR_BASE_URL", env).rstrip("/")
    server_id = _required_env("IT_PORTAL_COLLECTOR_SERVER_ID", env)
    # Garante scope padrão se o operador não setar S2S_SCOPE.
    merged = dict(env)
    if not (merged.get("S2S_SCOPE") or "").strip():
        merged["S2S_SCOPE"] = DEFAULT_SCOPE

    provider = ClientCredentialsTokenProvider.from_env(merged)
    token = provider.get_token()
    body = payload if payload is not None else build_observation_payload()
    request = build_ingest_request(
        base_url=base_url,
        server_id=server_id,
        token=token,
        body=body,
        http_host=(env.get("IT_PORTAL_COLLECTOR_HTTP_HOST") or "").strip() or None,
    )
    opener = http_open or urllib.request.urlopen
    try:
        with opener(request, timeout=30) as response:
            raw = response.read()
            parsed = json.loads(raw) if raw else {}
            return {"http_status": getattr(response, "status", 201), "body": parsed}
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:500]
        raise SystemExit(
            f"Ingestão recusada: HTTP {exc.code} {detail!r}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Falha de rede ao enviar observação: {exc.reason}") from exc


def main(argv: list[str] | None = None) -> int:
    _ = argv
    result = submit_observation()
    # Não imprime token/secret — apenas status HTTP e corpo da API.
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
