#!/usr/bin/env python3
"""E2E HTTP — valida persistência incremental no stream (user_persisted, assistant_pending).

Uso:
  python3 scripts/validate_stream_incremental_persistence_e2e.py
  SMOKE_BASE_URL=http://localhost SMOKE_USER=rober SMOKE_PASSWORD=1234 python3 scripts/validate_stream_incremental_persistence_e2e.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


BASE_URL = _env("SMOKE_BASE_URL", "http://localhost")
REALM = _env("SMOKE_REALM", "delpi")
CLIENT_ID = _env("SMOKE_CLIENT_ID", "delpi-central")
USERNAME = _env("SMOKE_USER", "rober")
PASSWORD = _env("SMOKE_PASSWORD", "1234")
CHAT_PREFIX = _env("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat")


def _fetch_token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "username": USERNAME,
            "password": PASSWORD,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}/auth/realms/{REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Token ausente: {payload}")
    return token


def _json_request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _first_agent_id(token: str) -> str:
    agents = _json_request("GET", f"{BASE_URL}{CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and agent.get("visibility") == "system":
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


@dataclass
class SseEvent:
    event: str
    data: dict


def _parse_sse(raw: str) -> list[SseEvent]:
    events: list[SseEvent] = []
    current_event = "message"
    data_lines: list[str] = []

    for line in raw.splitlines():
        if line.startswith("event:"):
            current_event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())
        elif line == "" and data_lines:
            payload = json.loads("\n".join(data_lines))
            events.append(SseEvent(event=current_event, data=payload))
            data_lines = []
            current_event = "message"

    if data_lines:
        payload = json.loads("\n".join(data_lines))
        events.append(SseEvent(event=current_event, data=payload))

    return events


def _stream_message(token: str, session_id: str, message: str, agent_id: str) -> list[SseEvent]:
    body = json.dumps({"message": message, "agentId": agent_id}).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{CHAT_PREFIX}/sessions/{session_id}/messages/stream",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return _parse_sse(raw)


def main() -> int:
    failed = 0
    token = _fetch_token()
    agent_id = _first_agent_id(token)
    session = _json_request(
        "POST",
        f"{BASE_URL}{CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "E2E persistência incremental", "agentId": agent_id},
    )
    session_id = str(session["id"])

    message = "olá"
    events = _stream_message(token, session_id, message, agent_id)
    event_names = [event.event for event in events]

    checks = [
        ("user_persisted presente", "user_persisted" in event_names),
        ("assistant_pending presente", "assistant_pending" in event_names),
        ("done presente", "done" in event_names),
        (
            "user_persisted antes de activity",
            "user_persisted" in event_names
            and "activity" in event_names
            and event_names.index("user_persisted") < event_names.index("activity"),
        ),
        (
            "assistant_pending antes de done",
            "assistant_pending" in event_names
            and event_names.index("assistant_pending") < event_names.index("done"),
        ),
    ]

    user_event = next((event for event in events if event.event == "user_persisted"), None)
    user_message_id = (user_event.data.get("messageId") if user_event else None)

    messages_payload = _json_request(
        "GET",
        f"{BASE_URL}{CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )
    items = messages_payload if isinstance(messages_payload, list) else messages_payload.get("items", [])
    user_rows = [row for row in items if row.get("role") == "user"]
    assistant_rows = [row for row in items if row.get("role") == "assistant"]

    checks.extend(
        [
            ("mensagem user no histórico", len(user_rows) >= 1),
            ("mensagem assistant no histórico", len(assistant_rows) >= 1),
            (
                "user messageId bate com user_persisted",
                user_message_id is not None and any(str(row.get("id")) == str(user_message_id) for row in user_rows),
            ),
            (
                "conteúdo user persistido",
                any(str(row.get("content") or "") == message for row in user_rows),
            ),
        ]
    )

    for label, ok in checks:
        if ok:
            print(f"OK {label}")
        else:
            failed += 1
            print(f"FAIL {label}", file=sys.stderr)

    if failed:
        print(f"\nEventos SSE: {event_names}", file=sys.stderr)
        return 1

    print(f"\n{len(checks)}/{len(checks)} OK (E2E persistência incremental, user={USERNAME})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
