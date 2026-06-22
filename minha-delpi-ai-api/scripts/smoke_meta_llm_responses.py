#!/usr/bin/env python3
"""Smoke — perguntas meta (perfil, capacidades, assistente) sem placeholders nem resposta vazia."""

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

_CASES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "quem sou eu?",
        ("@",),
        ("[nome]", "[email]", "não informado"),
    ),
    (
        "o que você pode fazer?",
        ("posso", "ajud", "rag", "consult"),
        ("[nome]", "[capacidade]", "não sei o que fazer"),
    ),
    (
        "quem é você?",
        ("assistente", "delpi", "agente"),
        ("[nome]", "openai", "chatgpt", "2019"),
    ),
)


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


def _validate_answer(question: str, answer: str, must_contain: tuple[str, ...], must_not: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    lowered = answer.lower()

    if not answer.strip():
        errors.append("resposta vazia")

    for marker in must_not:
        if marker.lower() in lowered:
            errors.append(f"contém «{marker}»")

    if must_contain and not any(token.lower() in lowered for token in must_contain):
        errors.append(f"sem nenhum dos tokens esperados: {must_contain}")

    return errors


def main() -> int:
    try:
        token = _fetch_token()
        agent_id = _first_agent_id(token)
        session = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
            token=token,
            body={"title": "Smoke meta LLM", "agentId": agent_id},
        )
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError) as err:
        print(f"FAIL setup: {err}", file=sys.stderr)
        return 1

    failures = 0

    for question, must_contain, must_not in _CASES:
        try:
            response = _request(
                "POST",
                f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session['id']}/messages",
                token=token,
                body={"message": question, "agentId": agent_id},
            )
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError) as err:
            print(f"FAIL [{question}]: {err}", file=sys.stderr)
            failures += 1
            continue

        answer = str(response.get("answer") or "")
        errors = _validate_answer(question, answer, must_contain, must_not)

        if errors:
            failures += 1
            print(f"FAIL [{question}]: {', '.join(errors)}", file=sys.stderr)
            print(answer[:400].replace("\n", " "), file=sys.stderr)
        else:
            print(f"OK [{question}] {answer[:160].replace(chr(10), ' ')}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
