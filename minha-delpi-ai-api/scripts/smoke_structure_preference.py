#!/usr/bin/env python3
"""Smoke — estrutura/BOM com preferências Texto (outline), Tabela e Árvore."""

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
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "90260149").strip()


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=300) as response:
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
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=10", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente disponível")


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"agentId": agent_id, "context": "geral"},
    )
    return str(payload["id"])


def _send(
    token: str,
    session_id: str,
    agent_id: str,
    message: str,
    *,
    response_format: str | None = None,
) -> dict:
    body = {"message": message, "agentId": agent_id}

    if response_format:
        body["responseFormat"] = response_format

    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body=body,
    )


def _set_response_format(token: str, session_id: str, response_format: str) -> None:
    _request(
        "PUT",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/memory/response-format",
        token=token,
        body={"responseFormat": response_format},
    )


def _structure_meta(response: dict) -> dict | None:
    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "").lower()

        if "/structure" in path and meta.get("ok"):
            return meta

    return None


def _text_markdown(meta: dict) -> str:
    text_presentation = meta.get("textPresentation") or {}
    return str(text_presentation.get("markdown") or "")


def _has_tree_outline(markdown: str) -> bool:
    if "**Composição**" not in markdown:
        return False

    if "```text" not in markdown and "```\n" not in markdown:
        return False

    return "├──" in markdown or "└──" in markdown


def main() -> int:
    failed = 0

    try:
        token = _fetch_token()
        print("OK login")
    except Exception as exc:
        print(f"FAIL login: {exc}", file=sys.stderr)
        return 1

    agent_id = _first_agent(token)
    message = f"estrutura {_PRODUCT}"

    # Cenário 1 — Texto com outline ASCII
    session_id = _create_session(token, agent_id)
    print(f"OK sessão turno text {session_id}")

    resp = _send(token, session_id, agent_id, message, response_format="text")
    meta = _structure_meta(resp)

    if not meta:
        print("FAIL [turno text] sem toolCall de estrutura", file=sys.stderr)
        failed += 1
    else:
        decision = meta.get("presentationDecision") or {}
        markdown = _text_markdown(meta)
        print(
            f"OK [turno text] path={meta.get('path')} "
            f"selected={decision.get('selected')!r}"
        )

        if decision.get("selected") != "text":
            print("FAIL [turno text] selected não é text", file=sys.stderr)
            failed += 1

        if not _has_tree_outline(markdown):
            print("FAIL [turno text] markdown sem outline ASCII em bloco text", file=sys.stderr)
            failed += 1

        if not isinstance(meta.get("treePresentation"), dict):
            print("WARN [turno text] treePresentation ausente (lazy árvore)", file=sys.stderr)

    # Cenário 2 — Tabela explícita
    session_id = _create_session(token, agent_id)
    print(f"OK sessão turno table {session_id}")

    resp = _send(token, session_id, agent_id, message, response_format="table")
    meta = _structure_meta(resp)

    if not meta:
        print("FAIL [turno table] sem toolCall de estrutura", file=sys.stderr)
        failed += 1
    else:
        decision = meta.get("presentationDecision") or {}
        presentation = meta.get("presentation") or {}
        print(
            f"OK [turno table] path={meta.get('path')} "
            f"selected={decision.get('selected')!r} presentation={presentation.get('type')!r}"
        )

        if meta.get("preferredFormat") != "table" or decision.get("selected") != "table":
            print("FAIL [turno table] metadata não reflete tabela", file=sys.stderr)
            failed += 1

        if presentation.get("type") != "table":
            print("FAIL [turno table] presentation primária não é tabela", file=sys.stderr)
            failed += 1

    # Cenário 3 — Árvore nativa
    session_id = _create_session(token, agent_id)
    print(f"OK sessão turno tree {session_id}")

    resp = _send(token, session_id, agent_id, message, response_format="tree")
    meta = _structure_meta(resp)

    if not meta:
        print("FAIL [turno tree] sem toolCall de estrutura", file=sys.stderr)
        failed += 1
    else:
        decision = meta.get("presentationDecision") or {}
        presentation = meta.get("presentation") or {}
        print(
            f"OK [turno tree] path={meta.get('path')} "
            f"selected={decision.get('selected')!r} presentation={presentation.get('type')!r}"
        )

        if meta.get("preferredFormat") != "tree" or decision.get("selected") != "tree":
            print("FAIL [turno tree] metadata não reflete árvore", file=sys.stderr)
            failed += 1

        if presentation.get("type") != "tree":
            tree_pres = meta.get("treePresentation") or {}

            if tree_pres.get("type") != "tree":
                print("FAIL [turno tree] presentation primária não é árvore", file=sys.stderr)
                failed += 1

    # Cenário 4 — preferência Texto na sessão + refinamento em tabela
    session_id = _create_session(token, agent_id)
    _set_response_format(token, session_id, "text")
    print(f"OK sessão memória text + refinamento {session_id}")

    first = _send(token, session_id, agent_id, message)
    first_meta = _structure_meta(first)

    if not first_meta:
        print("FAIL [refinamento] estrutura inicial sem tool", file=sys.stderr)
        failed += 1
    else:
        markdown = _text_markdown(first_meta)

        if not _has_tree_outline(markdown):
            print("FAIL [refinamento] turno 1 sem outline ASCII", file=sys.stderr)
            failed += 1

    follow = _send(token, session_id, agent_id, "mostre o último resultado em tabela")
    follow_meta = _structure_meta(follow)

    if not follow_meta:
        print("FAIL [refinamento] follow-up sem tool metadata", file=sys.stderr)
        failed += 1
    else:
        decision = follow_meta.get("presentationDecision") or {}
        presentation = follow_meta.get("presentation") or {}
        print(
            f"OK [refinamento] turno 2 path={follow_meta.get('path')} "
            f"preferred={follow_meta.get('preferredFormat')!r} "
            f"selected={decision.get('selected')!r} presentation={presentation.get('type')!r}"
        )

        if "/structure" not in str(follow_meta.get("path") or "").lower():
            print("FAIL [refinamento] não reutilizou rota de estrutura", file=sys.stderr)
            failed += 1

        if follow_meta.get("preferredFormat") != "table" or decision.get("selected") != "table":
            print("FAIL [refinamento] metadata não reflete tabela", file=sys.stderr)
            failed += 1

        if presentation.get("type") != "table":
            print("FAIL [refinamento] presentation primária não é tabela", file=sys.stderr)
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
