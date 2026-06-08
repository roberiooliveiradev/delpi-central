#!/usr/bin/env python3
"""Smoke E2E — 10 perguntas operacionais variadas (roteamento + tool + UX).

Valida que o chat Minha DELPI:
- chama a rota api-delpi esperada (tool ok);
- não cai em desambiguação genérica («Escolha uma opção»);
- não vaza erros técnicos nem rótulos em inglês nos KPIs financeiros;
- expõe resumo humanizado em PT (content ou humanizedSummary).

Uso (host com gateway na porta 80):
  python3 minha-delpi-ai-api/scripts/smoke_operational_intelligence_e2e.py

Uso (dentro do container / rede Docker):
  docker exec delpi-minha-delpi-ai-api python scripts/smoke_operational_intelligence_e2e.py

Variáveis opcionais:
  SMOKE_BASE_URL    (padrão http://localhost)
  SMOKE_USER        (padrão rober)
  SMOKE_PASSWORD    (padrão 1234)
  SMOKE_CHAT_PREFIX (padrão /apps/minha-delpi-ai/api/chat)
  SMOKE_PAUSE_SEC   (pausa entre cenários; padrão 2 — evita HTTP 429)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get(
    "SMOKE_CHAT_PREFIX",
    "/apps/minha-delpi-ai/api/chat",
).strip()
_PAUSE_SEC = float(os.environ.get("SMOKE_PAUSE_SEC", "2"))

_CLARIFY_MARKERS = (
    "escolha uma opção",
    "o que você quer ver sobre o produto",
)
_TECH_ERROR_MARKERS = (
    "has no attribute",
    "traceback",
    "internal server error",
    "erro interno",
    "got multiple values for argument",
)
_ENGLISH_KPI_MARKERS = ("gross revenue", "returns:", "branch: filial")


@dataclass(frozen=True)
class Scenario:
    id: str
    domain: str
    message: str
    path_fragment: str
    extra_checks: Callable[[str, dict], tuple[bool, str]] | None = None


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

    if "receita bruta" not in lowered and "rol" not in lowered and "r$" not in lowered:
        return False, "sem indicador financeiro em PT"

    return True, ""


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        id="P01",
        domain="produto / faturamento",
        message="Quanto já foi faturado do produto 90260015?",
        path_fragment="/sales/billing",
    ),
    Scenario(
        id="P02",
        domain="produto / status fabril",
        message="Qual o status completo na fábrica do produto 90269002 hoje?",
        path_fragment="/factory-status",
    ),
    Scenario(
        id="P03",
        domain="financeiro / ROL",
        message="Qual foi o ROL da empresa em março de 2026?",
        path_fragment="/financial/rol",
        extra_checks=_financial_pt_checks,
    ),
    Scenario(
        id="P04",
        domain="produto / estoque",
        message="Qual o saldo disponível do produto 10080033 na filial 01?",
        path_fragment="/stock",
    ),
    Scenario(
        id="P05",
        domain="produto / estrutura",
        message="mostre a estrutura do produto 90260123",
        path_fragment="/structure",
    ),
    Scenario(
        id="P06",
        domain="suprimentos / CPV",
        message="Qual o CPV da empresa?",
        path_fragment="/supplies/cpv",
    ),
    Scenario(
        id="P07",
        domain="produto / fornecedores",
        message="quem fornece o produto 10080022?",
        path_fragment="/suppliers",
    ),
    Scenario(
        id="P08",
        domain="produto / where-used",
        message="onde é usado o produto 90260149?",
        path_fragment="/parents",
    ),
    Scenario(
        id="P09",
        domain="produto / compras",
        message="mostre as compras do produto 90260015",
        path_fragment="/purchases",
    ),
    Scenario(
        id="P10",
        domain="financeiro / PMR",
        message="Qual o PMR da empresa?",
        path_fragment="/financial/pmr",
    ),
)


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


def _evaluate(scenario: Scenario, response: dict) -> tuple[bool, str]:
    meta = _tool_meta(response)
    path = str(meta.get("path") or "")
    content = _effective_content(response, meta)

    if not path:
        error = str(meta.get("error") or "").strip()
        detail = f"sem tool execute_external_action"

        if error:
            detail = f"{detail}; error={error!r}"

        return False, detail

    if scenario.path_fragment.lower() not in path.lower():
        return False, f"path={path!r} (esperado *{scenario.path_fragment}*)"

    checker = scenario.extra_checks or _default_checks
    ok, reason = checker(content, meta)

    if not ok:
        snippet = re.sub(r"\s+", " ", content[:160])
        return False, f"{reason}; snippet={snippet!r}"

    return True, f"path={path}"


def main() -> int:
    print(f"Smoke operacional E2E — base={_BASE_URL} user={_USERNAME}")
    print(f"Cenários: {len(SCENARIOS)} (pausa {_PAUSE_SEC}s entre turnos)\n")

    token = _token()
    agent_id = _agent_id(token)
    failed = 0

    for index, scenario in enumerate(SCENARIOS):
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
        print(f"{failed}/{len(SCENARIOS)} cenário(s) falharam", file=sys.stderr)
        return 1

    print(f"Todos os {len(SCENARIOS)} cenários passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
