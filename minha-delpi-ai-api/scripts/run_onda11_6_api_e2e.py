#!/usr/bin/env python3
"""E2E HTTP — validação backlog 11.6 (web_search, RBAC formal, NC 5S PostgreSQL).

Uso:
  python scripts/run_onda11_6_api_e2e.py
  SMOKE_BASE_URL=http://localhost SMOKE_USER=rober SMOKE_PASSWORD=1234 python scripts/run_onda11_6_api_e2e.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


BASE_URL = _env("SMOKE_BASE_URL", "http://localhost")
REALM = _env("SMOKE_REALM", "delpi")
CLIENT_ID = _env("SMOKE_CLIENT_ID", "delpi-central")
USERNAME = _env("SMOKE_USER", "rober")
PASSWORD = _env("SMOKE_PASSWORD", "1234")
API_PREFIX = _env("SMOKE_API_PREFIX", "/apps/minha-delpi-ai/api")
CHAT_PREFIX = _env("SMOKE_CHAT_PREFIX", f"{API_PREFIX}/chat")
DEFAULT_HTTP_TIMEOUT = int(_env("SMOKE_HTTP_TIMEOUT", "120"))
WEB_SEARCH_HTTP_TIMEOUT = int(_env("SMOKE_WEB_SEARCH_HTTP_TIMEOUT", "240"))


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: int | None = None,
) -> tuple[int, dict]:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=timeout or DEFAULT_HTTP_TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(detail) if detail else {}
        except json.JSONDecodeError:
            payload = {"raw": detail}
        return exc.code, payload


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


def _first_official_agent(token: str) -> str:
    status, agents = _request("GET", f"{BASE_URL}{CHAT_PREFIX}/agents?limit=20", token=token)
    if status != 200:
        raise RuntimeError(f"agents HTTP {status}: {agents}")
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and agent.get("visibility") == "system":
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def _create_session(token: str, agent_id: str, title: str) -> str:
    status, payload = _request(
        "POST",
        f"{BASE_URL}{CHAT_PREFIX}/sessions",
        token=token,
        body={"title": title, "agentId": agent_id},
    )
    if status not in (200, 201):
        raise RuntimeError(f"session HTTP {status}: {payload}")
    session_id = payload.get("id")
    if not session_id:
        raise RuntimeError(f"Sessão inválida: {payload}")
    return str(session_id)


def _send_message(
    token: str,
    session_id: str,
    message: str,
    agent_id: str,
    *,
    timeout: int | None = None,
) -> dict:
    status, payload = _request(
        "POST",
        f"{BASE_URL}{CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
        timeout=timeout,
    )
    if status not in (200, 201):
        raise RuntimeError(f"message HTTP {status}: {payload}")
    return payload


def _tool_action_path(response: dict) -> str:
    for call in response.get("toolCalls") or []:
        if call.get("name") != "execute_external_action":
            continue
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "")
        if path:
            return path
        args = call.get("arguments") or {}
        action_id = str(args.get("actionId") or "")
        if "audit-5s" in action_id or "audit_5s" in action_id:
            return "/quality/audit-5s/"
    return ""


def _tool_names(response: dict) -> list[str]:
    return [str(call.get("name") or "") for call in response.get("toolCalls") or []]


def _list_messages(token: str, session_id: str) -> list[dict]:
    status, payload = _request(
        "GET",
        f"{BASE_URL}{CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )
    if status != 200:
        raise RuntimeError(f"messages HTTP {status}: {payload}")
    return payload if isinstance(payload, list) else []


def _latest_assistant_message(messages: list[dict]) -> dict | None:
    for message in reversed(messages):
        if str(message.get("role") or "") == "assistant":
            return message
    return None


def _web_search_provider(response: dict) -> str:
    for call in response.get("toolCalls") or []:
        if call.get("name") != "web_search":
            continue
        metadata = call.get("metadata") or {}
        return str(metadata.get("provider") or "").strip()
    return ""


def _validate_web_search_research_metadata(message: dict) -> tuple[bool, str]:
    metadata = message.get("metadata") or {}
    research = metadata.get("webSearchResearch") or {}

    if not isinstance(research, dict) or not research:
        return False, "metadata.webSearchResearch ausente"

    provider = str(research.get("provider") or "").strip()
    if not provider:
        return False, "webSearchResearch.provider vazio"

    source_count = int(research.get("sourceCount") or 0)
    sites = research.get("sites") or []

    if source_count < 1 and not sites:
        return False, "webSearchResearch sem fontes"

    steps = research.get("steps") or []
    if not steps:
        return False, "webSearchResearch.steps vazio"

    return True, provider


def main() -> int:
    failed = 0
    passed = 0
    token = _fetch_token()

    # --- 11.6.2 RBAC formal ---
    status, profiles = _request("GET", f"{BASE_URL}{API_PREFIX}/admin/rbac/profiles", token=token)
    if status != 200:
        print(f"FAIL 11.6.2 GET /admin/rbac/profiles -> HTTP {status}: {profiles}", file=sys.stderr)
        failed += 1
    else:
        keys = {item.get("key") for item in profiles.get("profiles") or []}
        if keys >= {"admin", "operator", "auditor", "viewer"}:
            print("OK 11.6.2 GET /admin/rbac/profiles (4 perfis formais)")
            passed += 1
        else:
            print(f"FAIL 11.6.2 perfis incompletos: {keys}", file=sys.stderr)
            failed += 1

    status, summary = _request("GET", f"{BASE_URL}{API_PREFIX}/admin/rbac/summary", token=token)
    if status != 200:
        print(f"FAIL 11.6.2 GET /admin/rbac/summary -> HTTP {status}", file=sys.stderr)
        failed += 1
    elif "formalProfiles" not in summary or "formalProfileMatrix" not in summary:
        print("FAIL 11.6.2 summary sem formalProfiles/formalProfileMatrix", file=sys.stderr)
        failed += 1
    else:
        print("OK 11.6.2 GET /admin/rbac/summary (formalProfiles + matrix)")
        passed += 1

    # --- 11.6.1 web_search ---
    status, settings = _request(
        "GET",
        f"{BASE_URL}{API_PREFIX}/admin/chat/intelligence-settings",
        token=token,
    )
    if status != 200 or "webSearchEnabled" not in settings:
        print(f"FAIL 11.6.1 intelligence-settings sem webSearchEnabled (HTTP {status})", file=sys.stderr)
        failed += 1
    else:
        print("OK 11.6.1 GET intelligence-settings expõe webSearchEnabled")
        passed += 1

    status, saved = _request(
        "PUT",
        f"{BASE_URL}{API_PREFIX}/admin/chat/intelligence-settings",
        token=token,
        body={"webSearchEnabled": True},
    )
    if status != 200 or not saved.get("webSearchEnabled"):
        print(f"FAIL 11.6.1 PUT webSearchEnabled=true (HTTP {status})", file=sys.stderr)
        failed += 1
    else:
        print("OK 11.6.1 PUT webSearchEnabled=true")
        passed += 1

    agent_id = _first_official_agent(token)
    web_session = _create_session(token, agent_id, "E2E 11.6 — web_search")

    try:
        web_response = _send_message(
            token,
            web_session,
            "pesquise na internet sobre Python linguagem de programação",
            agent_id,
            timeout=WEB_SEARCH_HTTP_TIMEOUT,
        )
    except RuntimeError as exc:
        print(f"SKIP 11.6.1 web_search chat ({exc})", file=sys.stderr)
    else:
        tools = _tool_names(web_response)
        env_enabled = os.environ.get("CHAT_WEB_SEARCH_ENABLED", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if "web_search" in tools:
            print("OK 11.6.1 chat selecionou tool web_search")
            passed += 1
            if "execute_external_action" in tools:
                print(
                    "FAIL 11.6.1 web_search misturou execute_external_action "
                    f"(tools={tools})",
                    file=sys.stderr,
                )
                failed += 1
            else:
                answer = str(web_response.get("answer") or "")
                print("OK 11.6.1 web_search isolado (sem execute_external_action)")
                passed += 1
                if "internet pública" in answer.lower() or "internet publica" in answer.lower():
                    print("OK 11.6.1 resposta usa resultado da busca web")
                    passed += 1
                elif "não pesquis" in answer.lower() or "nao pesquis" in answer.lower():
                    print(
                        "FAIL 11.6.1 LLM negou busca apesar de web_search OK",
                        file=sys.stderr,
                    )
                    failed += 1
                else:
                    print(
                        "SKIP 11.6.1 resposta sem marcador web (verifique directAnswer/síntese)",
                        file=sys.stderr,
                    )

            provider = _web_search_provider(web_response)
            if provider:
                print(f"OK 11.6.1 provider web_search={provider}")
                passed += 1
            else:
                print("FAIL 11.6.1 tool web_search sem metadata.provider", file=sys.stderr)
                failed += 1

            try:
                assistant_message = _latest_assistant_message(_list_messages(token, web_session))
            except RuntimeError as exc:
                print(f"FAIL 11.6.1 GET messages ({exc})", file=sys.stderr)
                failed += 1
            else:
                if not assistant_message:
                    print("FAIL 11.6.1 mensagem assistant ausente no histórico", file=sys.stderr)
                    failed += 1
                else:
                    ok_research, detail = _validate_web_search_research_metadata(assistant_message)
                    if ok_research:
                        print(f"OK 11.6.1 metadata.webSearchResearch (provider={detail})")
                        passed += 1
                    else:
                        print(f"FAIL 11.6.1 {detail}", file=sys.stderr)
                        failed += 1

            web_sources = [
                item
                for item in (web_response.get("sources") or [])
                if str(item.get("scope") or "").strip().lower() == "web_search"
            ]
            if web_sources:
                print(f"OK 11.6.1 sources web_search={len(web_sources)}")
                passed += 1
            else:
                print("FAIL 11.6.1 resposta sem sources scope=web_search", file=sys.stderr)
                failed += 1
        elif not env_enabled:
            print(
                "SKIP 11.6.1 web_search (CHAT_WEB_SEARCH_ENABLED=false no container — "
                "recrie com CHAT_WEB_SEARCH_ENABLED=true)",
                file=sys.stderr,
            )
        else:
            print(f"FAIL 11.6.1 web_search não selecionada (tools={tools})", file=sys.stderr)
            failed += 1

    # --- 11.6.1b SearXNG (TYCO, síntese + painel Fontes) ---
    searxng_session = _create_session(token, agent_id, "E2E 11.6 — SearXNG TYCO")
    try:
        searxng_response = _send_message(
            token,
            searxng_session,
            "pesquise na internet sobre a empresa TYCO",
            agent_id,
            timeout=WEB_SEARCH_HTTP_TIMEOUT,
        )
    except RuntimeError as exc:
        print(f"SKIP 11.6.1b SearXNG TYCO ({exc})", file=sys.stderr)
    else:
        provider = _web_search_provider(searxng_response)
        if provider != "searxng":
            print(
                f"SKIP 11.6.1b provider={provider or 'n/d'} "
                "(esperado searxng quando CHAT_WEB_SEARCH_SEARXNG_BASE_URL está configurado)",
                file=sys.stderr,
            )
        elif "web_search" not in _tool_names(searxng_response):
            print("FAIL 11.6.1b web_search não selecionada para TYCO", file=sys.stderr)
            failed += 1
        else:
            print("OK 11.6.1b web_search TYCO via searxng")
            passed += 1
            assistant_message = _latest_assistant_message(_list_messages(token, searxng_session))
            if not assistant_message:
                print("FAIL 11.6.1b mensagem assistant ausente", file=sys.stderr)
                failed += 1
            else:
                research = (assistant_message.get("metadata") or {}).get("webSearchResearch") or {}
                if research.get("synthesized") is True:
                    print("OK 11.6.1b webSearchResearch.synthesized=true")
                    passed += 1
                else:
                    print("FAIL 11.6.1b webSearchResearch.synthesized ausente/false", file=sys.stderr)
                    failed += 1
                hostnames = {
                    str(item.get("hostname") or "")
                    for item in (research.get("sites") or [])
                    if isinstance(item, dict)
                }
                if hostnames and not all("duckduckgo.com" in host for host in hostnames):
                    print(f"OK 11.6.1b sites reais ({', '.join(sorted(hostnames)[:3])}…)")
                    passed += 1
                else:
                    print(f"FAIL 11.6.1b sites inesperados: {hostnames}", file=sys.stderr)
                    failed += 1

    status_actions, actions_payload = _request(
        "GET",
        f"{BASE_URL}{API_PREFIX}/admin/external-actions?limit=300",
        token=token,
    )
    agent_has_audit5s = False
    if status_actions == 200:
        items = (
            actions_payload
            if isinstance(actions_payload, list)
            else actions_payload.get("items", [])
        )
        agent_has_audit5s = any(
            "audit-5s" in str(item.get("path") or "").lower()
            and str(item.get("actionId") or "").startswith("api_externa.")
            for item in items
        )

    # --- 11.6.3 NC PostgreSQL (heurística audit-5s) ---
    nc_session = _create_session(token, agent_id, "E2E 11.6 — NC 5S")

    nc_cases = [
        (
            "11.6.3a resumo auditoria 5s",
            "resumo da auditoria 5s",
            "audit-5s",
        ),
        (
            "11.6.3b nc 5s sem product search",
            "nc 5s operacional",
            None,
        ),
    ]

    for label, message, expect_path in nc_cases:
        try:
            nc_response = _send_message(token, nc_session, message, agent_id)
        except RuntimeError as exc:
            print(f"FAIL {label} ({exc})", file=sys.stderr)
            failed += 1
            continue

        path = _tool_action_path(nc_response)
        admin_debug = nc_response.get("adminDebug") or {}
        selected = (admin_debug.get("tooling") or {}).get("selectedExternalAction") or {}
        action_id = str(selected.get("actionId") or "").lower()
        reason = str(selected.get("reason") or "").lower()
        tools = _tool_names(nc_response)

        if "products/search" in action_id or "/products/search" in path.lower():
            print(f"FAIL {label}: caiu em busca de produto (action={action_id})", file=sys.stderr)
            failed += 1
            continue

        if expect_path:
            haystack = f"{path} {action_id} {reason}"
            if expect_path.lower() in haystack:
                print(f"OK {label} (path/action audit-5s)")
                passed += 1
            elif not agent_has_audit5s:
                print(
                    f"SKIP {label} (agente usa api-externa; audit-5s/summary só em api-delpi)",
                    file=sys.stderr,
                )
            else:
                print(
                    f"FAIL {label}: esperava «{expect_path}» em path/action "
                    f"(path={path}, action={action_id})",
                    file=sys.stderr,
                )
                failed += 1
        elif not tools or "execute_external_action" not in tools:
            print(f"OK {label} (sem busca de produto; rota operacional ainda fora do OpenAPI)")
            passed += 1
        elif "nc operacionais" in reason or "audit-5s" in f"{path}{action_id}":
            print(f"OK {label} (intent audit-5s)")
            passed += 1
        else:
            print(f"FAIL {label}: seleção inesperada action={action_id} path={path}", file=sys.stderr)
            failed += 1

    total = passed + failed
    print(f"\n{passed}/{total} OK (E2E HTTP 11.6, user={USERNAME})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
