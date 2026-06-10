#!/usr/bin/env python3
"""Smoke stream — preferência tabela + refinamento."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

_BASE = os.environ.get("SMOKE_BASE_URL", "http://delpi-gateway")
_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat")
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "10080001")


def _token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": os.environ.get("SMOKE_CLIENT_ID", "delpi-central"),
            "username": os.environ.get("SMOKE_USER", "rober"),
            "password": os.environ.get("SMOKE_PASSWORD", "1234"),
        }
    ).encode()
    req = urllib.request.Request(
        f"{_BASE}/auth/realms/{os.environ.get('SMOKE_REALM', 'delpi')}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())["access_token"]


def _parse_sse(raw: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    current_event = "message"
    data_lines: list[str] = []

    for line in raw.splitlines():
        if line.startswith("event:"):
            current_event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())
        elif line == "" and data_lines:
            events.append((current_event, json.loads("\n".join(data_lines))))
            data_lines = []
            current_event = "message"

    if data_lines:
        events.append((current_event, json.loads("\n".join(data_lines))))

    return events


def _assistant_from_done(data: dict) -> dict:
    if isinstance(data.get("assistantMessage"), dict):
        return data["assistantMessage"]

    if isinstance(data.get("message"), dict):
        return data["message"]

    return {
        "content": data.get("answer"),
        "toolCalls": data.get("toolCalls"),
    }


def _stream(token: str, session_id: str, agent_id: str, message: str, *, response_format: str | None = None) -> dict:
    body: dict = {"message": message, "agentId": agent_id}

    if response_format:
        body["responseFormat"] = response_format

    req = urllib.request.Request(
        f"{_BASE}{_PREFIX}/sessions/{session_id}/messages/stream",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=300) as response:
        raw = response.read().decode("utf-8", errors="replace")

    events = _parse_sse(raw)
    done = next((payload for name, payload in reversed(events) if name == "done"), {})

    return _assistant_from_done(done)


def _meta(response: dict) -> dict:
    for call in response.get("toolCalls") or []:
        tool_meta = call.get("metadata") or {}

        if tool_meta.get("ok"):
            return tool_meta

    return {}


def main() -> int:
    token = _token()
    req = urllib.request.Request(
        f"{_BASE}{_PREFIX}/agents?limit=5",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        agents = json.loads(response.read())

    items = agents if isinstance(agents, list) else agents.get("items", [])
    agent = str(next(item["id"] for item in items if item.get("enabled")))

    req = urllib.request.Request(
        f"{_BASE}{_PREFIX}/sessions",
        data=json.dumps({"title": "smoke stream table", "agentId": agent}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        session_id = str(json.loads(response.read())["id"])

    first = _stream(token, session_id, agent, f"estoque do produto {_PRODUCT}", response_format="table")
    m1 = _meta(first)
    d1 = m1.get("presentationDecision") or {}
    print(
        "stream table:",
        f"preferred={m1.get('preferredFormat')!r}",
        f"selected={d1.get('selected')!r}",
        f"pres={(m1.get('presentation') or {}).get('type')!r}",
        f"content_len={len(first.get('content') or '')}",
    )

    if d1.get("selected") != "table" or (m1.get("presentation") or {}).get("type") != "table":
        print("FAIL stream table preference", file=sys.stderr)
        return 1

    second = _stream(token, session_id, agent, "mostre o último resultado em tabela")
    m2 = _meta(second)
    d2 = m2.get("presentationDecision") or {}
    content = str(second.get("content") or "")
    print(
        "stream refine:",
        f"tools={len(second.get('toolCalls') or [])}",
        f"selected={d2.get('selected')!r}",
        f"pres={(m2.get('presentation') or {}).get('type')!r}",
        f"content_head={content[:120]!r}",
    )

    if d2.get("selected") != "table" or "items:" in content.lower():
        print("FAIL stream refinement", file=sys.stderr)
        return 1

    if len(content) > 240:
        print(f"FAIL stream refinement content too long ({len(content)})", file=sys.stderr)
        return 1

    print("OK stream smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
