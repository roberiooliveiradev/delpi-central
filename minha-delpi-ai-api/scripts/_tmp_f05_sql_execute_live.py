#!/usr/bin/env python3
"""Live F05 — gerar SQL e pedir execução (frases naturais, multi-turno)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://delpi-gateway"
CHAT = "/apps/minha-delpi-ai/api/chat"


def req(method: str, url: str, token: str | None = None, body: dict | None = None, timeout: int = 240) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        err = ""
        try:
            err = exc.read().decode("utf-8", errors="replace")[:600]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {exc.code}: {err or exc.reason}") from exc


def answer_of(payload: dict) -> str:
    return str(payload.get("answer") or payload.get("content") or "").strip()


def debug_of(payload: dict) -> dict:
    d = payload.get("adminDebug")
    return d if isinstance(d, dict) else {}


def paths_of(payload: dict) -> list[str]:
    out: list[str] = []
    for call in payload.get("toolCalls") or []:
        if not isinstance(call, dict):
            continue
        meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
        path = str(meta.get("path") or "")
        if path:
            out.append(path)
    return out


def ops_of(payload: dict) -> list[str]:
    out: list[str] = []
    for call in payload.get("toolCalls") or []:
        if not isinstance(call, dict):
            continue
        meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
        op = str(meta.get("operationId") or "")
        if op:
            out.append(op)
    return out


def main() -> int:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": "delpi-central",
            "username": "rober",
            "password": "1234",
        }
    ).encode()
    with urllib.request.urlopen(
        urllib.request.Request(
            f"{BASE}/auth/realms/delpi/protocol/openid-connect/token",
            data=form,
            method="POST",
        ),
        timeout=30,
    ) as resp:
        token = json.loads(resp.read().decode())["access_token"]

    agents = req("GET", f"{BASE}{CHAT}/agents?limit=30", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    agent_id = next(
        (
            a["id"]
            for a in items
            if a.get("enabled") and "delpi" in str(a.get("name") or "").lower()
        ),
        None,
    ) or next(a["id"] for a in items if a.get("enabled"))

    session = req(
        "POST",
        f"{BASE}{CHAT}/sessions",
        token=token,
        body={"title": "F05 natural sql execute", "agentId": agent_id},
    )
    session_id = session["id"]
    print(f"session={session_id} agent={agent_id}")

    results: list[tuple[str, bool, str]] = []

    # --- Turn 1: authoring ---
    msg1 = "monta pra mim um sql dos 10 primeiros produtos do grupo 1008, sem executar"
    p1 = req(
        "POST",
        f"{BASE}{CHAT}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": msg1,
            "agentId": agent_id,
            "responseMode": "normal",
            "includeAdminDebug": True,
        },
    )
    a1 = answer_of(p1)
    d1 = debug_of(p1)
    intent1 = d1.get("intentRoute") or {}
    paths1 = paths_of(p1)
    low1 = a1.lower()
    ok1 = (
        ("```sql" in low1 or "select " in low1)
        and ("sb1010" in low1 or "sb1" in low1)
        and "sa1010" not in a1.split("```")[0].lower()
        and not any("schedule" in p.lower() for p in paths1)
        and len(paths1) == 0
    )
    print("=" * 72)
    print(f"T1 GENERATE | {'PASS' if ok1 else 'FAIL'}")
    print(f"msg: {msg1}")
    print(
        f"intent={intent1.get('intent')} sub={intent1.get('subIntent')} "
        f"decision={intent1.get('decision')} paths={paths1 or '-'}"
    )
    print("--- ANSWER ---")
    print(a1[:3500] if a1 else "(vazio)")
    print("--- END ---\n")
    results.append(("T1_generate", ok1, f"paths={paths1 or '-'} sql={'```sql' in low1}"))

    # --- Turn 2: execute follow-up (natural) ---
    msg2 = "agora executa esse sql aí e me mostra o resultado"
    p2 = req(
        "POST",
        f"{BASE}{CHAT}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": msg2,
            "agentId": agent_id,
            "responseMode": "normal",
            "includeAdminDebug": True,
        },
    )
    a2 = answer_of(p2)
    d2 = debug_of(p2)
    intent2 = d2.get("intentRoute") or {}
    paths2 = paths_of(p2)
    ops2 = ops_of(p2)
    tooling2 = d2.get("tooling") if isinstance(d2.get("tooling"), dict) else {}
    # toolCalls às vezes só em adminDebug.tooling
    merged_calls = list(p2.get("toolCalls") or [])
    if not merged_calls and isinstance(tooling2.get("toolCalls"), list):
        merged_calls = tooling2["toolCalls"]
    for call in merged_calls:
        if not isinstance(call, dict):
            continue
        meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
        path = str(meta.get("path") or "")
        op = str(meta.get("operationId") or "")
        if path and path not in paths2:
            paths2.append(path)
        if op and op not in ops2:
            ops2.append(op)
    low2 = a2.lower()
    executed_sql = any(
        "/data/sql" in p.lower() or ( "sql" in p.lower() and "schedule" not in p.lower())
        for p in paths2
    ) or any("sql" in op.lower() and "schedule" not in op.lower() for op in ops2)
    selected = tooling2.get("selectedExternalAction")
    if isinstance(selected, dict):
        aid = str(selected.get("actionId") or "").lower()
        if "sql" in aid and "schedule" not in aid:
            executed_sql = True
    for call in merged_calls:
        meta = (call or {}).get("metadata") or {}
        if str(meta.get("path") or "").lower().endswith("/sql") or "/data/sql" in str(
            meta.get("path") or ""
        ).lower():
            executed_sql = True
        body = meta.get("requestBody") or meta.get("body") or {}
        if isinstance(body, dict) and (body.get("sql") or body.get("query")):
            executed_sql = True
        args = (call or {}).get("arguments") or {}
        if isinstance(args, dict):
            inner = args.get("body") if isinstance(args.get("body"), dict) else {}
            if inner.get("sql") or inner.get("query"):
                executed_sql = True

    no_schedule = not any("schedule" in p.lower() for p in paths2)
    has_resultish = bool(a2) and (
        "1008" in a2
        or "produto" in low2
        or "linha" in low2
        or "registro" in low2
        or "resultado" in low2
        or "b1_" in low2
        or any(ch.isdigit() for ch in a2)
    )
    no_leak = "entrega obrigatória" not in low2
    ok2 = executed_sql and no_schedule and has_resultish and no_leak

    print("=" * 72)
    print(f"T2 EXECUTE | {'PASS' if ok2 else 'FAIL'}")
    print(f"msg: {msg2}")
    print(
        f"intent={intent2.get('intent')} sub={intent2.get('subIntent')} "
        f"decision={intent2.get('decision')}"
    )
    print(f"paths={paths2 or '-'} ops={ops2 or '-'}")
    print(f"toolCalls={json.dumps(p2.get('toolCalls') or [], ensure_ascii=False)[:1200]}")
    print("--- ANSWER ---")
    print(a2[:4000] if a2 else "(vazio)")
    print("--- END ---\n")
    results.append(
        (
            "T2_execute",
            ok2,
            f"sql_path={executed_sql} schedule={not no_schedule} "
            f"paths={paths2 or '-'} ans_len={len(a2)}",
        )
    )

    # --- Turn 3: oneshot prosa sem FROM não pode cair em REST de produção ---
    session_b = req(
        "POST",
        f"{BASE}{CHAT}/sessions",
        token=token,
        body={"title": "F05 one-shot execute", "agentId": agent_id},
    )
    sid_b = session_b["id"]
    msg3 = (
        "executa no banco esse select top 10 de produtos do grupo 1008 "
        "(SB1010, B1_COD, B1_DESC, B1_GRUPO)"
    )
    p3 = req(
        "POST",
        f"{BASE}{CHAT}/sessions/{sid_b}/messages",
        token=token,
        body={
            "message": msg3,
            "agentId": agent_id,
            "responseMode": "normal",
            "includeAdminDebug": True,
        },
    )
    a3 = answer_of(p3)
    paths3 = paths_of(p3)
    ops3 = ops_of(p3)
    d3 = debug_of(p3)
    intent3 = d3.get("intentRoute") or {}
    executed3 = any("/data/sql" in p.lower() or p.lower().rstrip("/").endswith("sql") for p in paths3)
    for call in p3.get("toolCalls") or []:
        meta = (call or {}).get("metadata") or {}
        if "/data/sql" in str(meta.get("path") or "").lower():
            executed3 = True
    wrong_rest = any(
        "/production/" in p.lower() or "/schedule/" in p.lower()
        for p in paths3
    )
    # Aceita: executou SQL, OU não executou REST errado (pede SQL completo / elabora).
    ok3 = (executed3 and not wrong_rest and bool(a3)) or (
        not executed3 and not wrong_rest and bool(a3) and "schedule" not in a3.lower()
    )
    print("=" * 72)
    print(f"T3 ONE-SHOT EXEC | {'PASS' if ok3 else 'FAIL'}")
    print(f"msg: {msg3}")
    print(
        f"intent={intent3.get('intent')} sub={intent3.get('subIntent')} "
        f"decision={intent3.get('decision')} paths={paths3 or '-'} ops={ops3 or '-'}"
    )
    print("--- ANSWER ---")
    print(a3[:3500] if a3 else "(vazio)")
    print("--- END ---\n")
    results.append(("T3_oneshot", ok3, f"paths={paths3 or '-'} sql={executed3} wrong_rest={wrong_rest}"))

    failed = [r for r in results if not r[1]]
    print("=== RESUMO F05 ===")
    for case_id, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'} {case_id}: {detail}")
    print(f"{len(results) - len(failed)}/{len(results)} PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
