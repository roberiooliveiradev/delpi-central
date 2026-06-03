#!/usr/bin/env python3
"""Smoke E2E — Especialista SQL (agente Minha DELPI) via API."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_TIMEOUT = int(os.environ.get("SMOKE_TIMEOUT", "240"))

# (id, message, checks)
_CHECKS: list[tuple[str, str, dict]] = [
    (
        "create_sa1",
        "Monte uma consulta para listar clientes ativos da tabela SA1, só código e nome, sem executar.",
        {
            "forbid_paths": ("/products/search",),
            "expect_paths_any": ("/system/tables",),
            "expect_answer_any": ("```sql", "a1_cod", "select"),
            "expect_intent_sub": "sql_generate",
            "forbid_stages": ("text_task",),
        },
    ),
    (
        "period_compare",
        "Compare vendas deste mês com o mês anterior por cliente, com variação percentual. Só monte o SQL, sem executar.",
        {
            "forbid_paths": ("/products/search",),
            "expect_answer_any": ("```sql", "cte", "with"),
        },
    ),
    (
        "ranking",
        "Monte um ranking dos 10 clientes com maior faturamento. SQL somente leitura, sem executar.",
        {
            "forbid_paths": ("/products/search",),
            "expect_answer_any": ("```sql", "rank", "row_number", "top"),
        },
    ),
    (
        "schema_columns",
        "Quais colunas existem na tabela SB1? Use a API de metadados se precisar.",
        {
            "forbid_paths": ("/products/search",),
            "expect_paths_any": ("/system/tables",),
        },
    ),
    (
        "schema_relations",
        "Como relacionar pedidos SC5 com clientes SA1? Valide no schema.",
        {
            "forbid_paths": ("/products/search",),
            "expect_paths_any": ("/system/tables",),
        },
    ),
    (
        "review_sql",
        "Revisa essa query:\n\nSELECT * FROM SA1010 a JOIN SC5010 p ON p.C5_CLIENTE = a.A1_COD",
        {
            "forbid_paths": ("/products/search",),
            "expect_answer_any": ("```sql", "select", "join", "risco", "select *"),
        },
    ),
    (
        "explain_sql",
        "Explique essa query: SELECT A1_COD, A1_NOME FROM SA1010 WHERE D_E_L_E_T_ = ''",
        {
            "forbid_paths": ("/products/search",),
            "expect_answer_any": ("objetivo", "filtro", "tabela", "select", "a1_"),
        },
    ),
    (
        "optimize",
        "Minha query está lenta, otimize sem executar: SELECT * FROM SD2010 WHERE D2_EMISSAO >= '20260101'",
        {
            "forbid_paths": ("/products/search",),
            "expect_answer_any": ("```sql", "índice", "indice", "filtro", "select", "performance"),
        },
    ),
    (
        "delete_blocked",
        "DELETE FROM SA1010 WHERE A1_COD = '000001'",
        {
            "forbid_paths": ("/products/search", "/data/sql"),
            "expect_answer_any": ("bloque", "segurança", "seguranca", "leitura", "select"),
        },
    ),
    (
        "postgres",
        "Monte a mesma consulta de clientes ativos da SA1 em PostgreSQL com LIMIT 20, sem executar.",
        {
            "forbid_paths": ("/products/search",),
            "expect_answer_any": ("```sql", "limit", "postgresql", "postgres"),
        },
    ),
]


def _request(
    method: str,
    url: str,
    *,
    token: str,
    body: dict | None = None,
    _token_holder: list[str] | None = None,
) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as response:
            raw = response.read().decode("utf-8")

            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        if exc.code == 401 and _token_holder is not None:
            _token_holder[0] = _fetch_token()
            headers["Authorization"] = f"Bearer {_token_holder[0]}"
            req = urllib.request.Request(url, data=data, headers=headers, method=method)

            with urllib.request.urlopen(req, timeout=_TIMEOUT) as response:
                raw = response.read().decode("utf-8")

                return json.loads(raw) if raw else {}

        raise


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


def _agent_id(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        name = str(agent.get("name") or "").lower()

        if "minha delpi" in name and agent.get("enabled", True):
            return str(agent["id"])

    for agent in items:
        if agent.get("enabled", True):
            return str(agent["id"])

    raise RuntimeError("Nenhum agente disponível")


def _tool_paths(response: dict) -> list[str]:
    paths: list[str] = []

    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or call.get("path") or "").strip().lower()

        if path:
            paths.append(path)

    return paths


def _admin_debug(response: dict) -> dict:
    debug = response.get("adminDebug")

    return debug if isinstance(debug, dict) else {}


def _check_case(case_id: str, response: dict, checks: dict) -> list[str]:
    errors: list[str] = []
    answer = str(response.get("answer") or "").lower()
    paths = _tool_paths(response)
    paths_joined = " ".join(paths)
    debug = _admin_debug(response)
    intel = debug.get("intelligence") if isinstance(debug.get("intelligence"), dict) else {}
    pipeline = intel.get("pipeline") if isinstance(intel.get("pipeline"), dict) else {}
    stages = pipeline.get("stages") or []
    intent_route = debug.get("intentRoute") if isinstance(debug.get("intentRoute"), dict) else {}
    sub_intent = str(intent_route.get("subIntent") or intent_route.get("router", {}).get("subIntent") or "")

    for forbidden in checks.get("forbid_paths") or ():
        if forbidden.lower() in paths_joined:
            errors.append(f"path proibido: {forbidden}")

    expect_paths = checks.get("expect_paths_any")

    if expect_paths and not any(token in paths_joined for token in expect_paths):
        errors.append(f"esperava path entre {expect_paths}, obteve {paths}")

    expect_answer = checks.get("expect_answer_any")

    if expect_answer and not any(token in answer for token in expect_answer):
        errors.append(f"resposta sem {expect_answer}")

    if checks.get("expect_intent_sub") and sub_intent != checks["expect_intent_sub"]:
        errors.append(f"subIntent={sub_intent!r} esperado {checks['expect_intent_sub']!r}")

    for forbidden_stage in checks.get("forbid_stages") or ():
        if forbidden_stage in stages:
            errors.append(f"stage proibido: {forbidden_stage}")

    if pipeline.get("operationalFastPath") and case_id in {"create_sa1", "period_compare", "ranking"}:
        errors.append("operationalFastPath=true em elaboração SQL")

    tooling = debug.get("tooling") if isinstance(debug.get("tooling"), dict) else {}
    selected = tooling.get("selectedExternalAction")

    if isinstance(selected, dict):
        reason = str(selected.get("reason") or "").lower()

        if "busca de produtos" in reason and case_id.startswith(("create", "period", "ranking", "schema")):
            errors.append(f"action errada: {reason[:80]}")

    return errors


def _run_incremental(token: str, agent_id: str, *, token_holder: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke SQL incremental", "agentId": agent_id},
        _token_holder=token_holder,
    )
    sid = session["id"]

    steps = [
        "Monte um SELECT de clientes da SA1 com A1_COD e A1_NOME, sem executar.",
        "Adicione a coluna cidade na consulta anterior, sem executar.",
    ]

    for index, message in enumerate(steps):
        active_token = token_holder[0] if token_holder else token
        response = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{sid}/messages",
            token=active_token,
            body={"message": message, "agentId": agent_id},
            _token_holder=token_holder,
        )
        answer = str(response.get("answer") or "").lower()
        paths = _tool_paths(response)

        if "/products/search" in " ".join(paths):
            errors.append(f"incremental passo {index + 1}: /products/search")

        if index == 1 and "cidade" not in answer and "a1_mun" not in answer and "municip" not in answer:
            errors.append(f"incremental passo 2: não mencionou cidade ({answer[:120]}...)")

    return errors


def main() -> int:
    started = time.time()
    failed = 0
    passed = 0

    print(f"Base: {_BASE_URL}{_CHAT_PREFIX}")

    try:
        token_holder = [_fetch_token()]
        print("Login: OK")
    except Exception as exc:
        print(f"FALHA login: {exc}", file=sys.stderr)
        return 1

    token = token_holder[0]

    try:
        agent_id = _agent_id(token)
        print(f"Agente: {agent_id}")
    except Exception as exc:
        print(f"FALHA agente: {exc}", file=sys.stderr)
        return 1

    for case_id, message, checks in _CHECKS:
        try:
            token = token_holder[0]
            session = _request(
                "POST",
                f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
                token=token,
                body={"title": f"Smoke SQL — {case_id}", "agentId": agent_id},
                _token_holder=token_holder,
            )
            token = token_holder[0]
            response = _request(
                "POST",
                f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session['id']}/messages",
                token=token,
                body={"message": message, "agentId": agent_id},
                _token_holder=token_holder,
            )
            case_errors = _check_case(case_id, response, checks)
            paths = _tool_paths(response)[:3]
            debug = _admin_debug(response)
            sub = (debug.get("intentRoute") or {}).get("subIntent", "?")

            if case_errors:
                failed += 1
                print(f"FAIL [{case_id}] sub={sub} paths={paths}")
                for err in case_errors:
                    print(f"       - {err}")
                snippet = re.sub(r"\s+", " ", str(response.get("answer") or ""))[:160]
                print(f"       answer: {snippet}...")
            else:
                passed += 1
                print(f"OK   [{case_id}] sub={sub} paths={paths or ['—']}")

        except Exception as exc:
            failed += 1
            print(f"FAIL [{case_id}] exceção: {exc}", file=sys.stderr)

    print("\n--- Edição incremental (mesma sessão) ---")

    try:
        inc_errors = _run_incremental(token_holder[0], agent_id, token_holder=token_holder)

        if inc_errors:
            failed += len(inc_errors)

            for err in inc_errors:
                print(f"FAIL [incremental] {err}")
        else:
            passed += 1
            print("OK   [incremental]")

    except Exception as exc:
        failed += 1
        print(f"FAIL [incremental] exceção: {exc}", file=sys.stderr)

    elapsed = time.time() - started
    total = passed + failed
    print(f"\nResumo: {passed}/{total} OK, {failed} falha(s), {elapsed:.0f}s")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
