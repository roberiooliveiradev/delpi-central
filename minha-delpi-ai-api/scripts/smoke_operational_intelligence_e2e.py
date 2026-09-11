#!/usr/bin/env python3
"""Smoke E2E — roteamento operacional (cenários em smoke_e2e_scenarios.json).

Uso:
  PYTHONPATH=minha-delpi-ai-api python3 minha-delpi-ai-api/scripts/smoke_operational_intelligence_e2e.py
  docker exec delpi-minha-delpi-ai-api python scripts/smoke_operational_intelligence_e2e.py
"""

from __future__ import annotations
from smoke_credentials import require_smoke_credentials

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable

from scripts.smoke_e2e_loader import SmokeScenario, load_suite, validation_markers

_SUITE = "operational_mixed"
_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME, _PASSWORD = require_smoke_credentials()
_CHAT_PREFIX = os.environ.get(
    "SMOKE_CHAT_PREFIX",
    "/apps/minha-delpi-ai/api/chat",
).strip()
_PAUSE_SEC = float(os.environ.get("SMOKE_PAUSE_SEC", "2"))

_CLARIFY_MARKERS = validation_markers("clarifyMarkers")
_TECH_ERROR_MARKERS = validation_markers("techErrorMarkers")
_ENGLISH_KPI_MARKERS = validation_markers("englishKpiMarkers")
_FINANCIAL_PT_INDICATORS = validation_markers("financialPtIndicators")


def _default_checks(content: str, meta: dict) -> tuple[bool, str]:
    lowered = content.lower()

    if any(marker in lowered for marker in _CLARIFY_MARKERS):
        return False, "desambiguação indevida"

    if any(marker in lowered for marker in _TECH_ERROR_MARKERS):
        return False, "erro técnico na resposta"

    if meta.get("ok") is not True:
        return False, "metadata.ok != true"

    if not content.strip():
        return False, "resposta vazia (sem content nem humanizedSummary)"

    return True, ""


def _financial_pt_checks(content: str, meta: dict) -> tuple[bool, str]:
    ok, reason = _default_checks(content, meta)

    if not ok:
        return ok, reason

    lowered = content.lower()

    if any(marker in lowered for marker in _ENGLISH_KPI_MARKERS):
        return False, "rótulo em inglês ou glossário técnico"

    if not any(marker in lowered for marker in _FINANCIAL_PT_INDICATORS):
        return False, "sem indicador financeiro em PT"

    return True, ""


_CHECKERS: dict[str, Callable[[str, dict], tuple[bool, str]]] = {
    "financial_pt": _financial_pt_checks,
}


def _checker_for(scenario: SmokeScenario) -> Callable[[str, dict], tuple[bool, str]] | None:
    if not scenario.checks:
        return None

    return _CHECKERS.get(scenario.checks)


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: int = 300,
) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc


def _token() -> str:
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
        raise RuntimeError("Token ausente na resposta do Keycloak")

    return str(token)


def _agent_id(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if not items:
        raise RuntimeError("Nenhum agente disponível")

    return str(items[0]["id"])


def _send_message(token: str, agent_id: str, message: str) -> dict:
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": f"Smoke E2E — {message[:48]}", "agentId": agent_id},
    )
    session_id = str(session["id"])

    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
    )


def _tool_meta(response: dict) -> dict:
    for call in response.get("toolCalls") or []:
        if call.get("name") != "execute_external_action":
            continue

        meta = call.get("metadata")

        if isinstance(meta, dict):
            return meta

    return {}


def _effective_content(response: dict, meta: dict) -> str:
    content = str(response.get("content") or "").strip()

    if content:
        return content

    humanized = meta.get("humanizedSummary")

    if not isinstance(humanized, dict):
        return ""

    parts: list[str] = []
    title = str(humanized.get("titulo") or "").strip()

    if title:
        parts.append(title)

    linhas = humanized.get("linhas")

    if isinstance(linhas, list):
        for line in linhas:
            text = str(line or "").strip()

            if text:
                parts.append(text)

    return "\n".join(parts)


def _evaluate(scenario: SmokeScenario, response: dict) -> tuple[bool, str]:
    meta = _tool_meta(response)
    path = str(meta.get("path") or "")
    content = _effective_content(response, meta)

    if not path:
        error = str(meta.get("error") or "").strip()
        detail = "sem tool execute_external_action"

        if error:
            detail = f"{detail}; error={error!r}"

        return False, detail

    if scenario.path_fragment.lower() not in path.lower():
        return False, f"path={path!r} (esperado *{scenario.path_fragment}*)"

    checker = _checker_for(scenario) or _default_checks
    ok, reason = checker(content, meta)

    if not ok:
        snippet = re.sub(r"\s+", " ", content[:160])
        return False, f"{reason}; snippet={snippet!r}"

    return True, f"path={path}"


def main() -> int:
    scenarios = load_suite(_SUITE)

    print(f"Smoke operacional E2E — base={_BASE_URL} user={_USERNAME}")
    print(f"Suite={_SUITE} cenários={len(scenarios)} (pausa {_PAUSE_SEC}s)\n")

    token = _token()
    agent_id = _agent_id(token)
    failed = 0

    for index, scenario in enumerate(scenarios):
        if index > 0 and _PAUSE_SEC > 0:
            time.sleep(_PAUSE_SEC)

        label = f"{scenario.id} [{scenario.domain}]"

        try:
            response = _send_message(token, agent_id, scenario.message)
            ok, detail = _evaluate(scenario, response)

            if ok:
                print(f"OK  {label} — {detail}")
            else:
                print(f"FAIL {label} — {detail}", file=sys.stderr)
                failed += 1
        except Exception as exc:
            print(f"FAIL {label} — {exc}", file=sys.stderr)
            failed += 1

    print()

    if failed:
        print(f"{failed}/{len(scenarios)} cenário(s) falharam", file=sys.stderr)
        return 1

    print(f"Todos os {len(scenarios)} cenários passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
