#!/usr/bin/env python3
"""Smoke live — simula usuário comum após fix new_intent / COUNT / isso.

Cobre SQL, rota operacional, texto e follow-ups. Avalia stage, tools e qualidade.

Uso (rede Docker):
  docker exec delpi-minha-delpi-ai-api python /app/scripts/smoke_new_intent_user_simulation.py
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

BASE = "http://delpi-gateway"
CHAT = "/apps/minha-delpi-ai/api/chat"


@dataclass
class CaseResult:
    family: str
    name: str
    ok: bool
    detail: str
    answer_preview: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


def fetch_token() -> str:
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
        return str(json.loads(resp.read().decode())["access_token"])


def req(
    method: str,
    url: str,
    token: str | None = None,
    body: dict | None = None,
    timeout: int = 240,
) -> dict:
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
            err = exc.read().decode("utf-8", errors="replace")[:800]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {exc.code}: {err or exc.reason}") from exc


def answer_of(payload: dict) -> str:
    return str(payload.get("answer") or payload.get("content") or "").strip()


def metadata_of(payload: dict) -> dict:
    meta = payload.get("metadata")
    return meta if isinstance(meta, dict) else {}


def debug_of(payload: dict) -> dict:
    d = payload.get("adminDebug")
    return d if isinstance(d, dict) else {}


def tool_calls_of(payload: dict) -> list[dict]:
    calls = payload.get("toolCalls")
    if isinstance(calls, list) and calls:
        return [c for c in calls if isinstance(c, dict)]
    tooling = debug_of(payload).get("tooling")
    if isinstance(tooling, dict) and isinstance(tooling.get("toolCalls"), list):
        return [c for c in tooling["toolCalls"] if isinstance(c, dict)]
    meta = metadata_of(payload)
    if isinstance(meta.get("toolCalls"), list):
        return [c for c in meta["toolCalls"] if isinstance(c, dict)]
    return []


def paths_ops(payload: dict) -> tuple[list[str], list[str], list[str]]:
    paths: list[str] = []
    ops: list[str] = []
    sqls: list[str] = []
    for call in tool_calls_of(payload):
        meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
        path = str(meta.get("path") or "").strip()
        op = str(meta.get("operationId") or "").strip()
        if path:
            paths.append(path)
        if op:
            ops.append(op)
        executed = str(meta.get("executedSql") or "").strip()
        if executed:
            sqls.append(executed)
        args = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
        body = args.get("body") if isinstance(args.get("body"), dict) else {}
        if isinstance(body, dict) and body.get("sql"):
            sqls.append(str(body.get("sql")))
        req_body = meta.get("requestBody") if isinstance(meta.get("requestBody"), dict) else {}
        if req_body.get("sql"):
            sqls.append(str(req_body.get("sql")))
    return paths, ops, sqls


def turn_grounding(payload: dict) -> dict:
    meta = metadata_of(payload)
    tg = meta.get("turnGrounding")
    if isinstance(tg, dict):
        return tg
    dbg = debug_of(payload)
    for key in ("turnGrounding", "intelligence"):
        node = dbg.get(key)
        if isinstance(node, dict) and isinstance(node.get("turnGrounding"), dict):
            return node["turnGrounding"]
        if key == "turnGrounding" and isinstance(node, dict):
            return node
    return {}


def send(token: str, session_id: str, agent_id: str, message: str) -> dict:
    return req(
        "POST",
        f"{BASE}{CHAT}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": message,
            "agentId": agent_id,
            "responseMode": "normal",
            "includeAdminDebug": True,
        },
    )


def new_session(token: str, agent_id: str, title: str) -> str:
    session = req(
        "POST",
        f"{BASE}{CHAT}/sessions",
        token=token,
        body={"title": title, "agentId": agent_id},
    )
    return str(session["id"])


def preview(text: str, limit: int = 500) -> str:
    body = re.sub(r"\s+", " ", str(text or "")).strip()
    return body[:limit] + ("…" if len(body) > limit else "")


def has_sql_count(sqls: list[str]) -> bool:
    blob = "\n".join(sqls).upper()
    return "COUNT(" in blob


def looks_like_template_recap(answer: str) -> bool:
    low = answer.lower()
    markers = (
        "foram retornados",
        "o formato dos dados sugere",
        "com base no último resultado",
    )
    hits = sum(1 for m in markers if m in low)
    return hits >= 2 or ("2 registro" in low and "foram retornados" in low)


def main() -> int:
    token = fetch_token()

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

    results: list[CaseResult] = []

    # ─── Família SQL ───────────────────────────────────────────────
    sid = new_session(token, agent_id, "smoke new_intent sql")
    print(f"\n=== SQL session={sid} ===")

    msg = "monta um sql dos 2 primeiros produtos do grupo 1008, sem executar"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    paths, ops, sqls = paths_ops(p)
    ok = ("```sql" in a.lower() or "select " in a.lower()) and len(paths) == 0
    results.append(
        CaseResult(
            "sql",
            "T1_author_sql",
            ok,
            f"paths={paths or '-'} has_sql={'select' in a.lower()}",
            preview(a),
        )
    )
    print(f"T1_author_sql {'PASS' if ok else 'FAIL'} | {results[-1].detail}")

    msg = "agora executa esse sql e me mostra o resultado"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    paths, ops, sqls = paths_ops(p)
    meta = metadata_of(p)
    executed = any("/data/sql" in x.lower() or x.lower().endswith("/sql") for x in paths) or bool(
        sqls
    )
    ok = executed and bool(a) and "entrega obrigatória" not in a.lower()
    results.append(
        CaseResult(
            "sql",
            "T2_execute_sql",
            ok,
            f"paths={paths or '-'} ops={ops or '-'} direct={meta.get('directResponse')}",
            preview(a),
            {"sqls": sqls[:1]},
        )
    )
    print(f"T2_execute_sql {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 240)}")

    msg = "traga a quantidade total de itens no grupo 1008"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    paths, ops, sqls = paths_ops(p)
    tg = turn_grounding(p)
    stage = tg.get("stage")
    follow = tg.get("followUp") if isinstance(tg.get("followUp"), dict) else {}
    decision = follow.get("decision")
    meta = metadata_of(p)
    template = looks_like_template_recap(a)
    count_sql = has_sql_count(sqls)
    sql_path = any("/data/sql" in x.lower() or x.lower().endswith("/sql") for x in paths)
    has_total_value = bool(
        re.search(r"\btotal\b", a, flags=re.I)
        and re.search(r"\d{2,}", a.replace(".", "").replace(",", ""))
    )
    ok = (
        stage != "grounded_narrate_recap"
        and not template
        and bool(a)
        and (count_sql or sql_path)
        and (has_total_value or ("189" in a.replace(".", "") or "total" in a.lower()))
    )
    results.append(
        CaseResult(
            "sql",
            "T3_count_total_new_intent",
            ok,
            (
                f"stage={stage!r} decision={decision!r} direct={meta.get('directResponse')} "
                f"paths={paths or '-'} count_sql={count_sql} template_recap={template}"
            ),
            preview(a),
            {"sqls": sqls[:2]},
        )
    )
    print(f"T3_count_total_new_intent {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 280)}")
    if sqls:
        print(f"  sql: {preview(sqls[0], 200)}")

    msg = "interprete o resultado da última consulta"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    tg = turn_grounding(p)
    stage = tg.get("stage")
    meta = metadata_of(p)
    ok = bool(a) and not looks_like_template_recap(a) and stage != "grounded_narrate_recap"
    results.append(
        CaseResult(
            "sql",
            "T4_interpret_insight",
            ok,
            f"stage={stage!r} direct={meta.get('directResponse')} len={len(a)}",
            preview(a),
        )
    )
    print(f"T4_interpret_insight {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 280)}")

    msg = "preciso disso amanha, quero o estoque do produto 10080001"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    paths, ops, sqls = paths_ops(p)
    tg = turn_grounding(p)
    stage = tg.get("stage")
    follow = tg.get("followUp") if isinstance(tg.get("followUp"), dict) else {}
    ok = stage != "grounded_narrate_recap" and not looks_like_template_recap(a)
    # Prefer stock route or any product tool, not SQL recap
    stockish = any(
        "stock" in x.lower() or "estoque" in x.lower() or "/products/" in x.lower()
        for x in paths + ops
    )
    if stockish:
        ok = True
    results.append(
        CaseResult(
            "sql",
            "T5_disso_then_stock_new_intent",
            ok,
            (
                f"stage={stage!r} decision={follow.get('decision')!r} "
                f"paths={paths or '-'} stockish={stockish}"
            ),
            preview(a),
        )
    )
    print(f"T5_disso_then_stock_new_intent {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 240)}")

    # ─── Família rota operacional ──────────────────────────────────
    sid = new_session(token, agent_id, "smoke new_intent route")
    print(f"\n=== ROUTE session={sid} ===")

    msg = "qual o rol deste mês?"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    paths, ops, sqls = paths_ops(p)
    rol_ok = any("rol" in x.lower() or "financial" in x.lower() for x in paths + ops) or (
        bool(a) and ("rol" in a.lower() or "r$" in a.lower() or "receita" in a.lower())
    )
    results.append(
        CaseResult(
            "route",
            "T6_rol_route",
            rol_ok and bool(a),
            f"paths={paths or '-'} ops={ops or '-'}",
            preview(a),
        )
    )
    print(f"T6_rol_route {'PASS' if results[-1].ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 240)}")

    msg = "e o estoque?"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    paths, ops, sqls = paths_ops(p)
    tg = turn_grounding(p)
    stage = tg.get("stage")
    follow = tg.get("followUp") if isinstance(tg.get("followUp"), dict) else {}
    ok = (
        follow.get("decision") == "new_intent"
        or stage is None
        or stage not in {"grounded_narrate_recap"}
    ) and not looks_like_template_recap(a)
    results.append(
        CaseResult(
            "route",
            "T7_topic_switch_estoque",
            ok,
            f"stage={stage!r} decision={follow.get('decision')!r} paths={paths or '-'}",
            preview(a),
        )
    )
    print(f"T7_topic_switch_estoque {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 240)}")

    msg = "resuma isso"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    tg = turn_grounding(p)
    stage = tg.get("stage")
    ok = bool(a) and stage in {"grounded_narrate_insight", "grounded_narrate_recap", None}
    # Must not be empty; insight preferred
    ok = bool(a) and len(a) > 40
    results.append(
        CaseResult(
            "route",
            "T8_resuma_isso",
            ok,
            f"stage={stage!r} len={len(a)}",
            preview(a),
        )
    )
    print(f"T8_resuma_isso {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 240)}")

    # ─── Família texto / identidade ────────────────────────────────
    sid = new_session(token, agent_id, "smoke new_intent text")
    print(f"\n=== TEXT session={sid} ===")

    msg = "quem é você?"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    paths, ops, sqls = paths_ops(p)
    meta = metadata_of(p)
    ok = bool(a) and len(paths) == 0 and (
        "delpi" in a.lower() or "assistente" in a.lower() or "sou" in a.lower()
    )
    results.append(
        CaseResult(
            "text",
            "T9_identity",
            ok,
            f"paths={paths or '-'} direct={meta.get('directResponse')} len={len(a)}",
            preview(a),
        )
    )
    print(f"T9_identity {'PASS' if ok else 'FAIL'} | {results[-1].detail}")

    msg = "bom dia"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    paths, ops, sqls = paths_ops(p)
    ok = bool(a) and len(paths) == 0
    results.append(
        CaseResult(
            "text",
            "T10_small_talk",
            ok,
            f"paths={paths or '-'} len={len(a)}",
            preview(a),
        )
    )
    print(f"T10_small_talk {'PASS' if ok else 'FAIL'} | {results[-1].detail}")

    msg = "deixe mais formal: preciso que envie o relatório hoje"
    p = send(token, sid, agent_id, msg)
    a = answer_of(p)
    paths, ops, sqls = paths_ops(p)
    ok = bool(a) and len(paths) == 0 and len(a) > 20
    results.append(
        CaseResult(
            "text",
            "T11_text_correction",
            ok,
            f"paths={paths or '-'} len={len(a)}",
            preview(a),
        )
    )
    print(f"T11_text_correction {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 200)}")

    # Bare isso after a short operational turn
    token = fetch_token()
    sid = new_session(token, agent_id, "smoke bare isso")
    print(f"\n=== DEIXIS session={sid} ===")
    p = send(token, sid, agent_id, "mostre o estoque do produto 10080001")
    a0 = answer_of(p)
    p = send(token, sid, agent_id, "isso")
    a = answer_of(p)
    tg = turn_grounding(p)
    stage = tg.get("stage")
    ok = bool(a) and stage in {
        "grounded_narrate_recap",
        "grounded_narrate_insight",
        None,
    }
    results.append(
        CaseResult(
            "deixis",
            "T12_bare_isso_recap_ok",
            ok,
            f"stage={stage!r} len={len(a)}",
            preview(a),
        )
    )
    print(f"T12_bare_isso_recap_ok {'PASS' if ok else 'FAIL'} | {results[-1].detail}")

    # ─── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("RESUMO")
    failed = [r for r in results if not r.ok]
    by_family: dict[str, list[CaseResult]] = {}
    for r in results:
        by_family.setdefault(r.family, []).append(r)
    for family, items in by_family.items():
        passed = sum(1 for i in items if i.ok)
        print(f"  {family}: {passed}/{len(items)}")
        for i in items:
            mark = "PASS" if i.ok else "FAIL"
            print(f"    [{mark}] {i.name} — {i.detail}")
            if not i.ok and i.answer_preview:
                print(f"           ans={i.answer_preview[:160]}")
    print(f"\nTOTAL: {len(results) - len(failed)}/{len(results)} PASS")
    if failed:
        print("FAILED:", ", ".join(f.name for f in failed))
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        raise
