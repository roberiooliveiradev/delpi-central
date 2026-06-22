#!/usr/bin/env python3
"""Smoke — «quem sou eu?» retorna nome e e-mail do /me (não «Não informado»)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()


def _request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as response:
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


def main() -> int:
    try:
        token = _fetch_token()
        agent_id = _first_agent_id(token)
        session = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
            token=token,
            body={"title": "Smoke identity profile", "agentId": agent_id},
        )
        response = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session['id']}/messages",
            token=token,
            body={"message": "quem sou eu?", "agentId": agent_id},
        )
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError) as err:
        print(f"FAIL: {err}", file=sys.stderr)
        return 1

    answer = str(response.get("answer") or "")
    if "Não informado" in answer:
        print("FAIL: resposta ainda contém «Não informado» para nome/e-mail", file=sys.stderr)
        print(answer[:400], file=sys.stderr)
        return 1

    if not answer.strip():
        print("FAIL: resposta vazia", file=sys.stderr)
        return 1

    placeholder_markers = ("[nome]", "[email]", "[nome do usuário]", "[email do usuário]")
    lowered = answer.lower()
    for marker in placeholder_markers:
        if marker in lowered:
            print(
                f"FAIL: resposta contém placeholder literal «{marker}»",
                file=sys.stderr,
            )
            print(answer[:400], file=sys.stderr)
            return 1

    if "@" not in answer and "Nome:" not in answer and "nome:" not in lowered:
        print(
            "FAIL: resposta não contém e-mail nem linha de nome do perfil",
            file=sys.stderr,
        )
        print(answer[:400], file=sys.stderr)
        return 1

    print("OK identity profile answer")
    print(answer[:320].replace("\n", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
