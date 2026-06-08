#!/usr/bin/env python3
"""Smoke HTTP — cancelamento de stream em andamento.

Uso (rede docker):
  docker exec delpi-minha-delpi-ai-api env SMOKE_BASE_URL=http://delpi-gateway \\
    python /app/scripts/smoke_cancel_stream_http.py
"""

from __future__ import annotations

import json
import os
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


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
) -> tuple[int, dict | list]:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            return response.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return exc.code, payload


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


def _pick_agent_id(token: str) -> str:
    _, agents = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20",
        token=token,
    )
    items = agents if isinstance(agents, list) else agents.get("items") or []

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente habilitado")


def _create_session(token: str, agent_id: str) -> str:
    _, payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke cancel stream", "agentId": agent_id},
    )
    session_id = str(payload.get("id") or "")

    if not session_id:
        raise RuntimeError(f"Sessão inválida: {payload}")

    return session_id


def _start_stream(token: str, session_id: str, agent_id: str) -> None:
    body = json.dumps({"message": "quem sou eu?", "agentId": agent_id}).encode("utf-8")
    request = urllib.request.Request(
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages/stream",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        for _ in range(3):
            response.readline()


def _delivery_status(messages: list, role: str) -> str | None:
    for message in reversed(messages):
        if message.get("role") != role:
            continue

        metadata = message.get("metadata") or {}
        delivery = metadata.get("delivery") or {}
        status = delivery.get("status")

        return str(status) if status else None

    return None


def main() -> int:
    token = _fetch_token()
    agent_id = _pick_agent_id(token)
    session_id = _create_session(token, agent_id)

    try:
        _start_stream(token, session_id, agent_id)
    except Exception as exc:
        print(f"WARN stream interrompido cedo: {exc}", file=sys.stderr)

    status, messages = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )

    if status != 200 or not isinstance(messages, list):
        print(f"FAIL histórico inválido: status={status} payload={messages}", file=sys.stderr)
        return 1

    user_status = _delivery_status(messages, "user")

    if user_status not in {"submitted", "processing", "cancelled"}:
        print(
            f"FAIL user delivery inesperado antes do cancel: {user_status} messages={messages}",
            file=sys.stderr,
        )
        return 1

    cancel_status, cancel_payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages/cancel",
        token=token,
    )

    if cancel_status != 200 or not isinstance(cancel_payload, dict) or not cancel_payload.get(
        "cancelled"
    ):
        print(
            f"FAIL cancel endpoint: session={session_id} user_status={user_status} "
            f"status={cancel_status} payload={cancel_payload}",
            file=sys.stderr,
        )
        return 1

    _, messages_after = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )

    if not isinstance(messages_after, list):
        print(f"FAIL histórico pós-cancel inválido: {messages_after}", file=sys.stderr)
        return 1

    user_status_after = _delivery_status(messages_after, "user")
    assistant_status_after = _delivery_status(messages_after, "assistant")

    if user_status_after != "cancelled":
        print(
            f"FAIL user não ficou cancelled: {user_status_after} messages={messages_after}",
            file=sys.stderr,
        )
        return 1

    if assistant_status_after == "generating":
        print(
            f"FAIL assistant generating ainda presente: messages={messages_after}",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK cancel stream session={session_id} "
        f"user_before={user_status} user_after={user_status_after}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
