#!/usr/bin/env python3
"""Smoke E2E — contexto multi-produto, formato de resposta e apresentação.

Uso:
  PYTHONPATH=. .venv/bin/python scripts/smoke_context_presentation_e2e.py

Variáveis:
  SMOKE_BASE_URL, SMOKE_USER (rober), SMOKE_PASSWORD (1234)
  SMOKE_PRODUCT_A, SMOKE_PRODUCT_B — códigos no contexto
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_PRODUCT_A = os.environ.get("SMOKE_PRODUCT_A", "90260140").strip()
_PRODUCT_B = os.environ.get("SMOKE_PRODUCT_B", "10080014").strip()


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=240) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _fetch_token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        raise RuntimeError(f"Token ausente: {payload}")

    return str(token)


def _first_agent(token: str) -> str:
    explicit = os.environ.get("SMOKE_AGENT_ID", "").strip()

    if explicit:
        return explicit

    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente")


def _ensure_smoke_actions(token: str, agent_id: str) -> None:
    """Garante actions de produto habilitadas e catálogo OpenAPI importado."""
    for action_id in (
        "api_delpi.products.get_product_stock",
        "api_delpi.products.get_product_structure",
        "api_delpi.products.get_product_prices",
    ):
        try:
            _request(
                "PUT",
                f"{_BASE_URL}{_CHAT_PREFIX}/agents/{agent_id}/actions",
                token=token,
                body={
                    "providerKey": "api-delpi",
                    "actionId": action_id,
                    "enabled": True,
                },
            )
        except Exception:
            pass

    try:
        _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/agents/{agent_id}/providers/api-delpi/import",
            token=token,
        )
    except Exception:
        pass


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke contexto + apresentação", "agentId": agent_id},
    )
    return str(payload["id"])


def _send(token: str, session_id: str, agent_id: str, message: str) -> dict:
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
    )


def _add_context_item(token: str, session_id: str, content: str) -> dict:
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/memory/context-items",
        token=token,
        body={"content": content},
    )


def _set_response_format(token: str, session_id: str, response_format: str) -> dict:
    return _request(
        "PUT",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/memory/response-format",
        token=token,
        body={"responseFormat": response_format},
    )


def _stock_paths(response: dict) -> list[str]:
    paths: list[str] = []

    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "")

        if "/stock" in path.lower():
            paths.append(path)

    return paths


def _preferred_formats(response: dict) -> list[str]:
    formats: list[str] = []

    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        preferred = str(meta.get("preferredFormat") or "").strip().lower()
        decision = meta.get("presentationDecision") or {}
        selected = str(decision.get("selected") or "").strip().lower()

        if preferred:
            formats.append(preferred)

        if selected and selected not in formats:
            formats.append(selected)

    return formats


def _humanized_has_english_keys(response: dict) -> bool:
    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        preview = str(meta.get("responsePreview") or meta.get("humanizedSummary") or "")

        if "sale_price=" in preview or "table_code=" in preview:
            return True

        humanized = meta.get("humanizedSummary")

        if isinstance(humanized, dict):
            joined = "\n".join(str(line) for line in (humanized.get("linhas") or []))

            if "sale_price=" in joined or "table_code=" in joined:
                return True

    text = str(response.get("answer") or "")

    return "sale_price=" in text or "table_code=" in text


def main() -> int:
    failed = 0

    try:
        token = _fetch_token()
        print("OK login")
    except Exception as exc:
        print(f"FAIL login: {exc}", file=sys.stderr)
        return 1

    agent_id = _first_agent(token)
    _ensure_smoke_actions(token, agent_id)
    session_id = _create_session(token, agent_id)
    print(f"OK sessão {session_id}")

    ctx_a = _add_context_item(token, session_id, _PRODUCT_A)
    chips = len(ctx_a.get("chips") or [])
    print(f"OK contexto produto A ({chips} chips)")

    ctx_b = _add_context_item(token, session_id, f"produto {_PRODUCT_B}")
    print("OK contexto produto B")

    stock_resp = _send(token, session_id, agent_id, "estoque")
    stock_paths = _stock_paths(stock_resp)
    codes_in_paths = {_PRODUCT_A in path or _PRODUCT_B in path for path in stock_paths}

    if len(stock_paths) >= 2:
        print(f"OK estoque multi-produto: {len(stock_paths)} consultas stock")
    elif len(stock_paths) == 1 and any(codes_in_paths):
        print(
            f"WARN estoque: apenas 1 consulta ({stock_paths[0]}). "
            "Verifique CHAT_MULTI_ACTION_ENABLED e workingMemory.",
            file=sys.stderr,
        )
        failed += 1
    else:
        print(f"FAIL estoque: toolCalls stock={stock_paths!r}", file=sys.stderr)
        failed += 1

    fmt_resp = _set_response_format(token, session_id, "tree")
    format_chips = [
        chip
        for chip in (fmt_resp.get("chips") or [])
        if str(chip.get("kind") or "") == "format"
    ]

    if format_chips:
        print(f"OK response-format tree: chip {format_chips[0].get('label')}")
    else:
        print("WARN response-format: chip de formato não retornado", file=sys.stderr)

    structure_resp = _send(token, session_id, agent_id, "estrutura")
    formats = _preferred_formats(structure_resp)

    if any(token in formats for token in ("tree", "arvore", "árvore")):
        print(f"OK estrutura com preferência árvore: {formats}")
    else:
        print(f"WARN estrutura preferredFormat={formats!r}", file=sys.stderr)

    price_resp = _send(token, session_id, agent_id, f"preço {_PRODUCT_A}")

    if _humanized_has_english_keys(price_resp):
        print("WARN preço ainda contém chaves em inglês no preview", file=sys.stderr)
        failed += 1
    else:
        print("OK preço sem sale_price=/table_code= no preview")

    _set_response_format(token, session_id, "text")
    text_resp = _send(token, session_id, agent_id, f"resumo de estoque do produto {_PRODUCT_A}")
    text_formats = _preferred_formats(text_resp)

    if "text" in text_formats:
        print(f"OK preferência texto ativa: {text_formats}")
    else:
        print(f"WARN preferência texto: formats={text_formats!r}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
