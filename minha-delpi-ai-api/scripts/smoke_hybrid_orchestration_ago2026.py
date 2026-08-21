#!/usr/bin/env python3
"""Smoke — orquestração híbrida (vago / schedule / leak).

Sem HTTP: valida serviços de domínio (sempre).
Com SMOKE_HTTP=1: envia «programação» e «programação de produção» ao chat.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _offline_checks() -> list[str]:
    from app.composition.content_composer import configure_domain_infrastructure_ports

    configure_domain_infrastructure_ports()

    from app.domain.services.chat_intent_router_service import ChatIntentRouterService
    from app.domain.services.chat_llm_synthesis_leak_guard_service import (
        ChatLlmSynthesisLeakGuardService,
    )
    from app.domain.services.chat_unclear_request_service import ChatUnclearRequestService

    failures: list[str] = []

    if ChatUnclearRequestService.classify("programação") != "ambiguous_domain":
        failures.append("programação deveria ser ambiguous_domain")

    answer = ChatUnclearRequestService.build_direct_answer(message="programação") or ""
    if not answer or "according to my instructions" in answer.lower():
        failures.append("clarify de programação inválido")

    route = ChatIntentRouterService.classify("programação de produção")
    if route.intent != "operational_query" or route.sub_intent != "schedule_today_lookup":
        failures.append(
            f"schedule classify falhou: {route.intent}/{route.sub_intent}/{route.reason}"
        )
    if not route.requires_tool:
        failures.append("schedule deveria requires_tool")

    leaked = (
        "According to my instructions, the user's message is vague. "
        "I should ask for clarification."
    )
    if not ChatLlmSynthesisLeakGuardService.needs_fallback(answer=leaked):
        failures.append("leak EN CoT não detectado")

    guarded = ChatLlmSynthesisLeakGuardService.guard_answer(answer=leaked, fallback=None)
    if "according to my instructions" in guarded.lower():
        failures.append("leak EN CoT não foi substituído")

    return failures


def _http_checks() -> list[str]:
    base = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
    realm = os.environ.get("SMOKE_REALM", "delpi").strip()
    client_id = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
    username = os.environ.get("SMOKE_USER", "rober").strip()
    password = os.environ.get("SMOKE_PASSWORD", "1234").strip()
    prefix = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
    failures: list[str] = []

    def request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
        headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": client_id,
            "username": username,
            "password": password,
        }
    ).encode("utf-8")
    token_req = urllib.request.Request(
        f"{base}/auth/realms/{realm}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(token_req, timeout=30) as response:
        token = json.loads(response.read().decode("utf-8")).get("access_token")
    if not token:
        return ["token ausente"]

    session = request(
        "POST",
        f"{base}{prefix}/sessions",
        token=token,
        body={"title": "smoke-hybrid-orchestration"},
    )
    session_id = str(session.get("id") or "")
    if not session_id:
        return ["session id ausente"]

    vague = request(
        "POST",
        f"{base}{prefix}/sessions/{session_id}/messages",
        token=token,
        body={"content": "programação", "responseMode": "normal"},
    )
    answer = str(vague.get("content") or vague.get("answer") or "").lower()
    if "according to my instructions" in answer or "<think" in answer:
        failures.append("HTTP programação vazou CoT EN")
    if not answer.strip():
        failures.append("HTTP programação sem resposta")

    schedule = request(
        "POST",
        f"{base}{prefix}/sessions/{session_id}/messages",
        token=token,
        body={"content": "programação de produção hoje", "responseMode": "normal"},
    )
    tools = schedule.get("toolCalls") or schedule.get("tools") or []
    meta = schedule.get("metadata") or {}
    admin = meta.get("adminDebug") or {}
    intelligence = admin.get("intelligence") or meta.get("intelligence") or {}
    tool_count = len(tools) if isinstance(tools, list) else int(
        intelligence.get("toolCount") or 0
    )
    if tool_count < 1:
        failures.append(
            f"HTTP schedule sem tools (toolCount={tool_count})"
        )

    return failures


def main() -> int:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)

    failures = _offline_checks()
    if os.environ.get("SMOKE_HTTP", "").strip() in {"1", "true", "yes"}:
        try:
            failures.extend(_http_checks())
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            failures.append(f"HTTP smoke falhou: {exc}")

    if failures:
        print("FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("OK hybrid orchestration smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
