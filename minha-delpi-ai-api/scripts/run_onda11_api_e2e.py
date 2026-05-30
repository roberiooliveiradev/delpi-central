#!/usr/bin/env python3
"""E2E HTTP — validação Onda 11 com usuário real (Keycloak + API chat).

Uso:
  python scripts/run_onda11_api_e2e.py
  SMOKE_BASE_URL=http://localhost SMOKE_USER=rober SMOKE_PASSWORD=1234 python scripts/run_onda11_api_e2e.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class Case:
    label: str
    message: str
    expect_in_answer: list[str] | None = None
    expect_not_in_answer: list[str] | None = None
    max_tool_calls: int | None = None
    action_contains: str | None = None
    skip_rag: bool | None = None
    session_id: str | None = None


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


BASE_URL = _env("SMOKE_BASE_URL", "http://localhost")
REALM = _env("SMOKE_REALM", "delpi")
CLIENT_ID = _env("SMOKE_CLIENT_ID", "delpi-central")
USERNAME = _env("SMOKE_USER", "rober")
PASSWORD = _env("SMOKE_PASSWORD", "1234")
CHAT_PREFIX = _env("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat")


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc


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


def _create_session(token: str, agent_id: str | None, title: str) -> str:
    body = {"title": title}
    if agent_id:
        body["agentId"] = agent_id
    payload = _request(
        "POST",
        f"{BASE_URL}{CHAT_PREFIX}/sessions",
        token=token,
        body=body,
    )
    session_id = payload.get("id")
    if not session_id:
        raise RuntimeError(f"Sessão inválida: {payload}")
    return str(session_id)


def _send_message(token: str, session_id: str, message: str, agent_id: str | None = None) -> dict:
    body: dict = {"message": message}
    if agent_id:
        body["agentId"] = agent_id
    return _request(
        "POST",
        f"{BASE_URL}{CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body=body,
    )


def _first_official_agent(token: str) -> str:
    agents = _request("GET", f"{BASE_URL}{CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and agent.get("visibility") == "system":
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def _check_case(case: Case, response: dict) -> list[str]:
    errors: list[str] = []
    answer = str(response.get("answer") or "")
    answer_lower = answer.lower()
    tool_calls = response.get("toolCalls") or []
    admin_debug = response.get("adminDebug") or {}
    intelligence = admin_debug.get("intelligence") or {}

    for needle in case.expect_in_answer or []:
        if needle.lower() not in answer_lower:
            errors.append(f"resposta deve conter «{needle}»")

    for forbidden in case.expect_not_in_answer or []:
        if forbidden.lower() in answer_lower:
            errors.append(f"resposta não deve conter «{forbidden}»")

    if case.max_tool_calls is not None and len(tool_calls) > case.max_tool_calls:
        errors.append(f"toolCalls <= {case.max_tool_calls} (foi {len(tool_calls)})")

    if case.action_contains:
        action_ids = [
            str((call.get("arguments") or {}).get("actionId") or "")
            for call in tool_calls
            if call.get("name") == "execute_external_action"
        ]
        needle = case.action_contains.lower()
        if not any(needle in action_id.lower() for action_id in action_ids):
            errors.append(f"actionId deve conter «{case.action_contains}» (foi {action_ids})")

    if case.skip_rag is not None:
        pipeline = admin_debug.get("pipeline") or {}
        intel_pipeline = intelligence.get("pipeline") or {}
        actual = intelligence.get("skipRag")
        if actual is None:
            actual = intel_pipeline.get("skipRag")
        if actual is None:
            actual = pipeline.get("skipRag")
        if actual is not case.skip_rag:
            errors.append(f"skipRag={case.skip_rag} (foi {actual})")

    if "[data atual]" in answer_lower or "[hoje + 1 dia]" in answer_lower:
        errors.append("resposta contém placeholder de data do LLM")

    return errors


def main() -> int:
    failed = 0
    token = _fetch_token()
    user = _request("GET", f"{BASE_URL}/core-api/me", token=token)
    if user.get("username") != USERNAME and user.get("email"):
        print(f"Aviso: /me retornou {user.get('email')}", file=sys.stderr)

    caps = _request("GET", f"{BASE_URL}{CHAT_PREFIX}/capabilities", token=token)
    if caps.get("knowledgeDocumentMaxChars") != 2_000_000:
        print(
            f"FAIL capabilities: knowledgeDocumentMaxChars={caps.get('knowledgeDocumentMaxChars')}",
            file=sys.stderr,
        )
        failed += 1
    else:
        print("OK capabilities knowledgeDocumentMaxChars=2000000")

    agent_id = _first_official_agent(token)
    utility_session = _create_session(token, agent_id, "Smoke Onda 11 — utilitário")
    ops_session = _create_session(token, agent_id, "Smoke Onda 11 — operacional")

    cases: list[Case] = [
        Case("U1 que horas são?", "que horas são?", expect_in_answer=[":"], max_tool_calls=0, skip_rag=True),
        Case("U2 que hors são?", "que hors são?", expect_in_answer=[":"], max_tool_calls=0, skip_rag=True),
        Case("U4 que dia é hoje?", "que dia é hoje?", expect_in_answer=["/"], max_tool_calls=0, skip_rag=True),
        Case("U5 que dia é amanhã?", "que dia é amanhã?", expect_in_answer=["amanhã"], max_tool_calls=0, skip_rag=True),
        Case("U6 que dia foi ontem?", "que dia foi ontem?", expect_in_answer=["ontem"], max_tool_calls=0, skip_rag=True),
        Case("U8 bo dia", "bo dia", max_tool_calls=0),
        Case("#1 estoque sem código", "estoque do produto", expect_in_answer=["código"], max_tool_calls=0, skip_rag=True, session_id=ops_session),
        Case("#4 quem te criou?", "quem te criou?", expect_in_answer=["minha delpi"], max_tool_calls=0, skip_rag=True, session_id=ops_session),
        Case("#5 olá", "olá", max_tool_calls=0, session_id=ops_session),
    ]

    optional_ops_cases: list[Case] = [
        Case(
            "#3 estoque código",
            "estoque do produto 10080022",
            action_contains="stock",
            max_tool_calls=1,
            skip_rag=True,
            session_id=ops_session,
        ),
    ]

    for case in cases:
        session_id = case.session_id or utility_session
        try:
            response = _send_message(token, session_id, case.message, agent_id=agent_id)
        except RuntimeError as exc:
            print(f"FAIL {case.label}: {exc}", file=sys.stderr)
            failed += 1
            continue

        errors = _check_case(case, response)
        if errors:
            failed += 1
            print(f"FAIL {case.label}: {case.message}", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            print(f"  answer: {str(response.get('answer') or '')[:180]}", file=sys.stderr)
        else:
            print(f"OK {case.label}")

    for case in optional_ops_cases:
        session_id = case.session_id or ops_session
        try:
            response = _send_message(token, session_id, case.message, agent_id=agent_id)
        except RuntimeError as exc:
            print(f"SKIP {case.label} (API externa indisponível: {exc})", file=sys.stderr)
            continue

        tool_calls = response.get("toolCalls") or []
        tool_meta = (tool_calls[0].get("metadata") or {}) if tool_calls else {}
        if tool_calls and not tool_meta.get("ok"):
            print(
                f"SKIP {case.label} (action executada mas API retornou erro — "
                "ambiente local com api-delpi off usa api-externa)",
                file=sys.stderr,
            )
            continue

        errors = _check_case(case, response)
        if errors:
            failed += 1
            print(f"FAIL {case.label}: {case.message}", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
        else:
            print(f"OK {case.label}")

    # Multi-turn KPI (#6b) exige rotas /supplies/* — só no provider api-delpi (omitido se desabilitado)
    kpi_session = _create_session(token, agent_id, "Smoke Onda 11 — KPI filial")
    kpi_first = _send_message(
        token,
        kpi_session,
        "qual o valor total de estoque da empresa",
        agent_id=agent_id,
    )
    first_calls = kpi_first.get("toolCalls") or []
    first_meta = (
        (first_calls[0].get("metadata") or {})
        if first_calls
        else {}
    )
    if first_meta.get("ok"):
        kpi_follow = _send_message(token, kpi_session, "filial 01", agent_id=agent_id)
        kpi_errors = _check_case(
            Case(
                "#6b KPI + filial curta",
                "filial 01",
                action_contains="stock",
                max_tool_calls=1,
                skip_rag=True,
            ),
            kpi_follow,
        )
        if kpi_errors:
            failed += 1
            print("FAIL #6b KPI + filial curta", file=sys.stderr)
            for err in kpi_errors:
                print(f"  - {err}", file=sys.stderr)
        else:
            print("OK #6b KPI + filial curta")
    else:
        print(
            "SKIP #6b KPI + filial curta (KPI /supplies/* requer provider api-delpi habilitado)",
            file=sys.stderr,
        )

    total = len(cases)
    passed = total - failed
    print(f"\n{passed}/{total} OK (E2E HTTP Onda 11, user={USERNAME})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
