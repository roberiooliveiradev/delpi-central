#!/usr/bin/env python3
"""Smoke — modos de resposta em product overview (rápida vs normal)."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
QUESTION = os.environ.get("SMOKE_QUESTION", "me fale do produto 10080045").strip()


def req(method, url, token=None, body=None, timeout=600):
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode()
        return json.loads(raw) if raw else {}


def main() -> int:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": "delpi-central",
            "username": os.environ.get("SMOKE_USER", "rober"),
            "password": os.environ.get("SMOKE_PASSWORD", "1234"),
        }
    ).encode()
    with urllib.request.urlopen(
        urllib.request.Request(
            f"{BASE}/auth/realms/delpi/protocol/openid-connect/token",
            data=form,
            method="POST",
        ),
        timeout=30,
    ) as response:
        token = json.loads(response.read())["access_token"]

    agents = req("GET", f"{BASE}{PREFIX}/agents?limit=5", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    agent_id = str(next(a["id"] for a in items if a.get("enabled")))

    results = []
    for mode in ("fast", "normal"):
        session = req(
            "POST",
            f"{BASE}{PREFIX}/sessions",
            token=token,
            body={"title": f"Smoke mode {mode}", "agentId": agent_id},
        )
        sid = session["id"]
        t0 = time.perf_counter()
        req(
            "POST",
            f"{BASE}{PREFIX}/sessions/{sid}/messages",
            token=token,
            body={"message": QUESTION, "agentId": agent_id, "responseMode": mode},
        )
        elapsed = round(time.perf_counter() - t0, 1)
        messages = req("GET", f"{BASE}{PREFIX}/sessions/{sid}/messages", token=token)
        msg_items = messages if isinstance(messages, list) else messages.get("items", [])
        assistant = next(m for m in reversed(msg_items) if m.get("role") == "assistant")
        pipeline = (assistant.get("metadata") or {}).get("intelligence", {}).get("pipeline", {})
        results.append(
            {
                "mode": mode,
                "elapsedSec": elapsed,
                "chars": len(str(assistant.get("content") or "")),
                "effect": pipeline.get("responseModeEffect"),
                "directResponse": pipeline.get("directResponse"),
            }
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))

    fast, normal = results
    if fast["effect"] != "presenter_direct":
        return 1
    if normal["effect"] != "llm_synthesis":
        return 1
    if normal["elapsedSec"] <= fast["elapsedSec"]:
        print("WARN: normal não ficou mais lento que fast (CPU/Ollama)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
