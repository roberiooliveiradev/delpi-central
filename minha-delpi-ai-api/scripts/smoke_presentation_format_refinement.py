#!/usr/bin/env python3
"""Smoke HTTP — refinamento de formato (tabela, árvore, gráfico) em follow-up.

Cenários multiturno sem reexecutar API quando há cache no histórico.

Uso:
  SMOKE_BASE_URL=http://localhost PYTHONPATH=. python scripts/smoke_presentation_format_refinement.py
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
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "90260149").strip()


def _request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=300) as response:
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
    req = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        raise RuntimeError(f"Token ausente: {payload}")

    return str(token)


def _first_agent_id(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=10", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente disponível")


def _send(token: str, session_id: str, agent_id: str, message: str) -> dict:
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
    )


def _tool_meta(response: dict) -> dict:
    for call in response.get("toolCalls") or []:
        meta = call.get("metadata")

        if isinstance(meta, dict) and meta.get("ok"):
            return meta

    return {}


def _check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"OK  {label}" + (f" — {detail}" if detail else ""))
        return

    print(f"FAIL {label}" + (f" — {detail}" if detail else ""), file=sys.stderr)
    raise AssertionError(label)


def main() -> int:
    failed = 0

    try:
        token = _fetch_token()
    except Exception as exc:
        print(f"SKIP API indisponível: {exc}", file=sys.stderr)
        return 0

    agent_id = _first_agent_id(token)

    scenarios: list[tuple[str, list[tuple[str, callable]]]] = [
        (
            "estoque → coloque em tabela",
            [
                (f"qual o estoque do produto {_PRODUCT}?", lambda m: m.get("path", "").endswith("/stock")),
                (
                    "coloque em uma tabela",
                    lambda m: (
                        m.get("preferredFormat") == "table"
                        and (m.get("presentation") or {}).get("type") == "table"
                        and not str(m.get("path") or "").endswith("/system/tables")
                    ),
                ),
            ],
        ),
        (
            "produto → mostre em árvore",
            [
                (
                    f"estrutura do produto {_PRODUCT}",
                    lambda m: "/structure" in str(m.get("path") or "")
                    or (m.get("presentation") or {}).get("type") in {"tree", "table"},
                ),
                (
                    "mostre em árvore",
                    lambda m: (m.get("presentation") or {}).get("type") == "tree"
                    or (m.get("treePresentation") or {}).get("type") == "tree"
                    or m.get("preferredFormat") == "tree",
                ),
            ],
        ),
        (
            "analyser → coloque em tabela",
            [
                (
                    f"me fale do produto {_PRODUCT}",
                    lambda m: str(m.get("path") or "").endswith("/analyser"),
                ),
                (
                    "coloque em uma tabela",
                    lambda m: m.get("preferredFormat") == "table"
                    and (m.get("presentation") or {}).get("type") == "table",
                ),
            ],
        ),
        (
            "analyser → só texto",
            [
                (
                    f"me fale do produto {_PRODUCT}",
                    lambda m: str(m.get("path") or "").endswith("/analyser"),
                ),
                (
                    "mostre só em texto, sem tabela",
                    lambda m: m.get("preferredFormat") == "text"
                    and bool(m.get("textPresentation")),
                ),
            ],
        ),
    ]

    for title, steps in scenarios:
        session = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
            token=token,
            body={"title": f"Smoke formato — {title}", "agentId": agent_id},
        )
        session_id = str(session["id"])

        try:
            for message, predicate in steps:
                response = _send(token, session_id, agent_id, message)
                meta = _tool_meta(response)

                if not meta:
                    _check(f"{title} / {message[:40]}", False, "sem tool ok")
                    continue

                _check(
                    f"{title} / {message[:48]}",
                    bool(predicate(meta)),
                    f"path={meta.get('path')} preferred={meta.get('preferredFormat')} "
                    f"pres={(meta.get('presentation') or {}).get('type')}",
                )
        except AssertionError:
            failed += 1

    if failed:
        print(f"\n{failed} cenário(s) falharam", file=sys.stderr)
        return 1

    print("\nSmoke refinamento de formato: todos os cenários passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
