#!/usr/bin/env python3
"""Smoke E2E — Especialista SQL (chat comum + agente Minha DELPI) via API."""

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
_MODE = os.environ.get("SMOKE_SQL_MODE", "both").strip().lower()
_ONLY = [item.strip() for item in os.environ.get("SMOKE_ONLY", "").split(",") if item.strip()]
_WARMUP = os.environ.get("SMOKE_WARMUP", "").strip().lower() in {"1", "true", "yes"}

# (id, message, checks)
_CHECKS: list[tuple[str, str, dict]] = [
    (
        "create_sa1",
        "Monte uma consulta para listar clientes ativos da tabela SA1, só código e nome, sem executar.",
        {
            "forbid_paths": ("/products/search",),
            "expect_paths_any": ("/system/tables",),
            "expect_paths_agent_only": True,
            "expect_answer_any": ("```sql", "a1_cod", "select"),
            "require_sql_block": True,
            "forbid_schema_catalog_only": True,
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
            "require_sql_block": True,
            "forbid_schema_catalog_only": True,
        },
    ),
    (
        "ranking",
        "Monte um ranking dos 10 clientes com maior faturamento. SQL somente leitura, sem executar.",
        {
            "forbid_paths": ("/products/search",),
            "expect_answer_any": ("```sql", "rank", "row_number", "top"),
            "require_sql_block": True,
            "forbid_schema_catalog_only": True,
        },
    ),
    (
        "schema_columns",
        "Quais colunas existem na tabela SB1? Use a API de metadados se precisar.",
        {
            "forbid_paths": ("/products/search",),
            "expect_paths_any": ("/system/tables",),
            "expect_paths_agent_only": True,
            "allow_schema_catalog_answer": True,
        },
    ),
    (
        "schema_relations",
        "Como relacionar pedidos SC5 com clientes SA1? Valide no schema.",
        {
            "forbid_paths": ("/products/search",),
            "expect_paths_any": ("/system/tables",),
            "expect_paths_agent_only": True,
            "require_sql_block": True,
            "forbid_schema_catalog_only": True,
        },
    ),
    (
        "review_sql",
        "Revisa essa query:\n\nSELECT * FROM SA1010 a JOIN SC5010 p ON p.C5_CLIENTE = a.A1_COD",
        {
            "forbid_paths": ("/products/search",),
            "expect_answer_any": ("```sql", "select", "join", "risco", "select *"),
            "require_sql_block": False,
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
            "require_sql_block": True,
            "forbid_schema_catalog_only": True,
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
            "require_sql_block": True,
            "forbid_schema_catalog_only": True,
        },
    ),
]

_INCREMENTAL_STEPS = [
    "Monte um SELECT de clientes da SA1 com A1_COD e A1_NOME, sem executar.",
    "Adicione a coluna cidade na consulta anterior, sem executar.",
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


def _agent_id(token: str, *, token_holder: list[str] | None = None) -> str:
    agents = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20",
        token=token,
        _token_holder=token_holder,
    )
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


def _message_body(message: str, agent_id: str | None) -> dict:
    body: dict = {"message": message}

    if agent_id:
        body["agentId"] = agent_id

    return body


def _session_body(title: str, agent_id: str | None) -> dict:
    body: dict = {"title": title}

    if agent_id:
        body["agentId"] = agent_id

    return body


def _check_case(
    case_id: str,
    response: dict,
    checks: dict,
    *,
    mode: str,
) -> list[str]:
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
    workspace = debug.get("workspace") if isinstance(debug.get("workspace"), dict) else {}
    skills = workspace.get("skills") if isinstance(workspace.get("skills"), dict) else {}

    for forbidden in checks.get("forbid_paths") or ():
        if forbidden.lower() in paths_joined:
            errors.append(f"path proibido: {forbidden}")

    expect_paths = checks.get("expect_paths_any")

    if expect_paths:
        if checks.get("expect_paths_agent_only") and mode == "common":
            if paths and not any(token in paths_joined for token in expect_paths):
                errors.append(f"chat comum não deve depender de API ({paths})")
        elif not any(token in paths_joined for token in expect_paths):
            if mode == "agent" or not checks.get("expect_paths_agent_only"):
                errors.append(f"esperava path entre {expect_paths}, obteve {paths}")

    expect_answer = checks.get("expect_answer_any")

    if expect_answer and not any(token in answer for token in expect_answer):
        errors.append(f"resposta sem {expect_answer}")

    if checks.get("require_sql_block") and "```sql" not in answer:
        errors.append("resposta sem bloco ```sql```")

    if checks.get("forbid_schema_catalog_only") and not checks.get("allow_schema_catalog_answer"):
        catalog_markers = ("colunas da tabela", "total de colunas")
        looks_like_catalog = any(marker in answer for marker in catalog_markers)

        if looks_like_catalog and "```sql" not in answer:
            errors.append("resposta exibiu catálogo de colunas sem entregar SQL")

        for call in response.get("toolCalls") or []:
            meta = call.get("metadata") or {}

            if meta.get("presentation") and checks.get("require_sql_block"):
                errors.append("toolCall ainda expõe presentation rica de schema (deveria ser interno)")

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

    if mode == "common" and not skills.get("sqlAuthoring"):
        errors.append("chat comum sem skill sqlAuthoring no workspace")

    if mode == "agent" and not workspace.get("actionsEnabled"):
        errors.append("agente sem actionsEnabled")

    return errors


def _run_suite(
    *,
    mode: str,
    label: str,
    agent_id: str | None,
    token_holder: list[str],
) -> tuple[int, int]:
    passed = 0
    failed = 0

    print(f"\n========== {label} (mesma sessão) ==========")

    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token_holder[0],
        body=_session_body(f"Smoke SQL E2E — {label}", agent_id),
        _token_holder=token_holder,
    )
    sid = session["id"]
    print(f"Sessão: {sid}")

    checks_list = _CHECKS
    if _ONLY:
        checks_list = [item for item in _CHECKS if item[0] in _ONLY]

    if _WARMUP and _ONLY:
        if "incremental" in _ONLY:
            warmup_cases = list(_CHECKS)
        else:
            warmup_ids = set(_ONLY)
            first_target = next((item[0] for item in _CHECKS if item[0] in warmup_ids), None)
            warmup_cases = []

            if first_target:
                for case_id, message, _checks in _CHECKS:
                    if case_id == first_target:
                        break

                    warmup_cases.append((case_id, message))

        for case_id, message in warmup_cases:
            print(f"WARM [{mode}:{case_id}] …")
            _request(
                "POST",
                f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{sid}/messages",
                token=token_holder[0],
                body=_message_body(message, agent_id),
                _token_holder=token_holder,
            )

    for case_id, message, checks in checks_list:
        prefix = f"{mode}:{case_id}"

        try:
            response = _request(
                "POST",
                f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{sid}/messages",
                token=token_holder[0],
                body=_message_body(message, agent_id),
                _token_holder=token_holder,
            )
            case_errors = _check_case(case_id, response, checks, mode=mode)
            paths = _tool_paths(response)[:3]
            debug = _admin_debug(response)
            sub = (debug.get("intentRoute") or {}).get("subIntent", "?")
            has_sql = "```sql" in str(response.get("answer") or "").lower()

            if case_errors:
                failed += 1
                print(f"FAIL [{prefix}] sub={sub} sql={has_sql} paths={paths}")
                for err in case_errors:
                    print(f"       - {err}")
                snippet = re.sub(r"\s+", " ", str(response.get("answer") or ""))[:200]
                print(f"       answer: {snippet}...")
            else:
                passed += 1
                print(f"OK   [{prefix}] sub={sub} sql={has_sql} paths={paths or ['—']}")

        except Exception as exc:
            failed += 1
            print(f"FAIL [{prefix}] exceção: {exc}", file=sys.stderr)

    if _ONLY and "incremental" not in _ONLY:
        return passed, failed

    print(f"\n--- Incremental ({label}, mesma sessão {sid[:8]}…) ---")

    for index, message in enumerate(_INCREMENTAL_STEPS):
        prefix = f"{mode}:incremental_{index + 1}"

        try:
            response = _request(
                "POST",
                f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{sid}/messages",
                token=token_holder[0],
                body=_message_body(message, agent_id),
                _token_holder=token_holder,
            )
            answer = str(response.get("answer") or "").lower()
            paths = _tool_paths(response)
            step_errors: list[str] = []

            if "/products/search" in " ".join(paths):
                step_errors.append("/products/search")

            if index == 1:
                if "```sql" not in answer:
                    step_errors.append("sem bloco ```sql```")
                if "cidade" not in answer and "a1_mun" not in answer and "municip" not in answer:
                    step_errors.append(f"sem cidade ({answer[:100]}...)")

            if step_errors:
                failed += len(step_errors)
                print(f"FAIL [{prefix}] {', '.join(step_errors)}")
            else:
                passed += 1
                print(f"OK   [{prefix}] sql={'```sql' in answer}")

        except Exception as exc:
            failed += 1
            print(f"FAIL [{prefix}] exceção: {exc}", file=sys.stderr)

    return passed, failed


def main() -> int:
    started = time.time()
    total_passed = 0
    total_failed = 0

    print(f"Base: {_BASE_URL}{_CHAT_PREFIX}")
    print(f"Modo: {_MODE}")

    try:
        token_holder = [_fetch_token()]
        print("Login: OK")
    except Exception as exc:
        print(f"FALHA login: {exc}", file=sys.stderr)
        return 1

    agent_id: str | None = None

    if _MODE in {"agent", "both", "all"}:
        try:
            agent_id = _agent_id(token_holder[0], token_holder=token_holder)
            print(f"Agente Minha DELPI: {agent_id}")
            p, f = _run_suite(
                mode="agent",
                label="Agente Minha DELPI",
                agent_id=agent_id,
                token_holder=token_holder,
            )
            total_passed += p
            total_failed += f
        except Exception as exc:
            print(f"FALHA suite agente: {exc}", file=sys.stderr)
            total_failed += 1

    if _MODE in {"common", "both", "all", "chat"}:
        p, f = _run_suite(
            mode="common",
            label="Chat comum (sem agentId)",
            agent_id=None,
            token_holder=token_holder,
        )
        total_passed += p
        total_failed += f

    elapsed = time.time() - started
    total = total_passed + total_failed
    print(f"\nResumo geral: {total_passed}/{total} OK, {total_failed} falha(s), {elapsed:.0f}s")

    return 1 if total_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
