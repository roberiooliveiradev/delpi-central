#!/usr/bin/env python3
"""Smoke HTTP — autoajuda Playbook 04 (respostas diretas sem LLM pesado).

Uso:
  PYTHONPATH=. python scripts/smoke_self_help_http.py
  SMOKE_BASE_URL=http://localhost SMOKE_USER=rober SMOKE_PASSWORD=1234 python scripts/smoke_self_help_http.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


def _default_smoke_base_url() -> str:
    explicit = os.environ.get("SMOKE_BASE_URL", "").strip()

    if explicit:
        return explicit

    if os.path.isdir("/app"):
        return "http://delpi-gateway"

    return "http://localhost"


_BASE_URL = _default_smoke_base_url().strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_CASES: tuple[tuple[str, tuple[str, ...], bool], ...] = (
    ("o que você pode fazer?", ("posso ajudar", "agente", "consult"), True),
    ("como consulto estoque?", ("estoque", "agente", "produto"), True),
    ("como anexo arquivo?", ("anexo", "arquivo", "clipe"), True),
    ("o que mudou?", ("novidade", "versão", "versao"), True),
    ("ajuda sobre lousa", ("lousa", "canvas"), True),
    ("como faço uma boa pergunta?", ("identificador", "formato", "três", "tres"), False),
)


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=180) as response:
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

    return str(payload["access_token"])


def _pick_agent_id(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items") or []

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    return ""


def _assistant_text(result: dict) -> str:
    direct = str(result.get("answer") or "").strip()

    if direct:
        return direct

    assistant = result.get("assistantMessage") or result.get("assistant") or {}

    return str(
        assistant.get("content")
        or assistant.get("text")
        or assistant.get("answer")
        or ""
    ).strip()


def _route_intent(result: dict) -> str | None:
    assistant = result.get("assistantMessage") or result.get("assistant") or {}
    metadata = assistant.get("metadata") or {}
    routing = metadata.get("intentRouting") or metadata.get("adminDebug", {}).get("intentRoute")

    if isinstance(routing, dict):
        return str(routing.get("intent") or routing.get("decision") or "").strip() or None

    return None


def main() -> int:
    try:
        token = _fetch_token()
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
        print(f"SKIP gateway/token ({exc})", file=sys.stderr)
        return 0

    agent_id = _pick_agent_id(token)

    if not agent_id:
        print("SKIP sem agente habilitado", file=sys.stderr)
        return 0

    failed = 0

    for message, expected_tokens, with_agent in _CASES:
        session_body: dict = {"title": f"Smoke self-help: {message[:40]}"}

        if with_agent:
            session_body["agentId"] = agent_id

        session = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
            token=token,
            body=session_body,
        )
        session_id = str(session.get("id") or "")

        if not session_id:
            print(f"FAIL sem session para {message!r}", file=sys.stderr)
            failed += 1
            continue

        message_body: dict = {"message": message}

        if with_agent:
            message_body["agentId"] = agent_id

        try:
            result = _request(
                "POST",
                f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
                token=token,
                body=message_body,
            )
        except urllib.error.HTTPError as exc:
            print(f"FAIL HTTP {exc.code} para {message!r}", file=sys.stderr)
            failed += 1
            continue

        text = _assistant_text(result).lower()
        intent = _route_intent(result)

        if not text:
            print(f"FAIL resposta vazia para {message!r}", file=sys.stderr)
            failed += 1
            continue

        if not any(token.lower() in text for token in expected_tokens):
            print(
                f"FAIL conteúdo para {message!r}: esperado um de {expected_tokens}; "
                f"trecho={text[:180]!r}",
                file=sys.stderr,
            )
            failed += 1
            continue

        if intent and intent not in {"self_help", "capabilities", "identity", "meta"}:
            if not re.search(r"estoque|anexo|lousa|novidade|pergunta", text):
                print(
                    f"WARN intent={intent} para {message!r} (resposta parece ok)",
                    file=sys.stderr,
                )

        metadata = (result.get("assistantMessage") or {}).get("metadata") or result.get(
            "metadata"
        ) or {}
        chips = metadata.get("helpFollowUpSuggestions")

        print(f"OK {message!r} intent={intent or '-'} chips={bool(chips)}")

    if failed:
        return 1

    print("Smoke self-help HTTP: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
