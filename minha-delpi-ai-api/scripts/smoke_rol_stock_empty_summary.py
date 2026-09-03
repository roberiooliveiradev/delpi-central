#!/usr/bin/env python3
"""Smoke live — ROL → estoque (sem herdar data) → prosa vazia sem card → resumo.

Uso:
  docker exec delpi-minha-delpi-ai-api python /app/scripts/smoke_rol_stock_empty_summary.py
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


def tool_calls_of(payload: dict) -> list[dict]:
    calls = payload.get("toolCalls")
    if isinstance(calls, list) and calls:
        return [c for c in calls if isinstance(c, dict)]
    meta = metadata_of(payload)
    if isinstance(meta.get("toolCalls"), list):
        return [c for c in meta["toolCalls"] if isinstance(c, dict)]
    return []


def paths_of(payload: dict) -> list[str]:
    paths: list[str] = []
    for call in tool_calls_of(payload):
        meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
        path = str(meta.get("path") or "").strip()
        if path:
            paths.append(path)
        args = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
        params = args.get("parameters") if isinstance(args.get("parameters"), dict) else {}
        code = str(params.get("code") or params.get("product_code") or "").strip()
        if code:
            paths.append(f"code={code}")
    return paths


def preview(text: str, limit: int = 420) -> str:
    body = re.sub(r"\s+", " ", str(text or "")).strip()
    return body[:limit] + ("…" if len(body) > limit else "")


def looks_like_asks_product_code(answer: str) -> bool:
    low = answer.lower()
    return any(
        token in low
        for token in (
            "informe o código",
            "informe o codigo",
            "código do produto",
            "codigo do produto",
            "informe o **código",
            "para consultar o **estoque**",
            "para consultar o estoque",
        )
    )


def mentions_date_as_product(answer: str, paths: list[str]) -> bool:
    blob = " ".join([answer, *paths])
    if re.search(r"(?:produto\s+|products/|/|/code=)20\d{2}(?:0[1-9]|1[0-2])(?:\d{2})?\b", blob):
        return True
    # Valor monetário / float ruidoso herdado como código (ex.: 4772289729999995).
    for path in paths:
        m = re.search(r"(?:products/|code=)(\d+)", path)
        if m and len(m.group(1)) > 12:
            return True
    return False


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

    sid = new_session(token, agent_id, "smoke rol→estoque→resumo")
    print(f"session={sid} agent={agent_id}")
    results: list[CaseResult] = []

    # T1 — ROL do mês corrente (julho/2026 no bug report)
    p = send(token, sid, agent_id, "qual o rol de julho/2026?")
    a = answer_of(p)
    paths = paths_of(p)
    meta = metadata_of(p)
    has_rol = any("rol" in x.lower() for x in paths) or "rol" in a.lower()
    ok = bool(a) and has_rol and not mentions_date_as_product(a, paths)
    results.append(
        CaseResult(
            "T1_rol_july",
            ok,
            f"paths={paths or '-'} errorHandling={bool(meta.get('errorHandling'))}",
            preview(a),
        )
    )
    print(f"T1_rol_july {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 260)}")

    # T2 — follow-up estoque sem código: NÃO herdar 202607
    p = send(token, sid, agent_id, "e o estoque?")
    a = answer_of(p)
    paths = paths_of(p)
    meta = metadata_of(p)
    err = meta.get("errorHandling") if isinstance(meta.get("errorHandling"), dict) else None
    used_date_product = mentions_date_as_product(a, paths)
    asks_code = looks_like_asks_product_code(a)
    ok = bool(a) and not used_date_product and (asks_code or not any("/stock" in x.lower() or "/estoque" in x.lower() for x in paths))
    # Preferência: pedir código; se consultar, não pode ser data-as-product
    if used_date_product:
        ok = False
    results.append(
        CaseResult(
            "T2_stock_asks_code_not_period",
            ok,
            (
                f"asks_code={asks_code} date_as_product={used_date_product} "
                f"paths={paths or '-'} errorHandling={err.get('type') if err else None}"
            ),
            preview(a),
        )
    )
    print(f"T2_stock_asks_code_not_period {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 280)}")

    # T3 — estoque de produto real (pode ser vazio); prosa sem card genérico se explicar
    p = send(token, sid, agent_id, "estoque do produto 10080001")
    a = answer_of(p)
    paths = paths_of(p)
    meta = metadata_of(p)
    err = meta.get("errorHandling") if isinstance(meta.get("errorHandling"), dict) else None
    empty_phrases = any(
        t in a.lower()
        for t in ("nenhum registro", "não retornou", "nao retornou", "sem saldo", "sem estoque")
    )
    # Se prosa longa explica vazio → errorHandling deve ser None
    prose_explains = empty_phrases and len(a.strip()) >= 80
    ok_card = (err is None) if prose_explains else True
    ok = bool(a) and ("10080001" in a or any("10080001" in x for x in paths) or "estoque" in a.lower()) and ok_card
    results.append(
        CaseResult(
            "T3_stock_product_no_redundant_card",
            ok,
            (
                f"paths={paths or '-'} empty_prose={empty_phrases} "
                f"errorHandling={err.get('type') if err else None} prose_explains={prose_explains}"
            ),
            preview(a),
        )
    )
    print(f"T3_stock_product_no_redundant_card {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 280)}")

    # T4 — resumo: não reabrir card de vazio
    p = send(token, sid, agent_id, "resuma isso")
    a = answer_of(p)
    meta = metadata_of(p)
    err = meta.get("errorHandling") if isinstance(meta.get("errorHandling"), dict) else None
    paths = paths_of(p)
    ok = bool(a) and len(a) >= 40 and err is None
    results.append(
        CaseResult(
            "T4_summary_no_empty_card",
            ok,
            f"errorHandling={err.get('type') if err else None} paths={paths or '-'} len={len(a)}",
            preview(a),
        )
    )
    print(f"T4_summary_no_empty_card {'PASS' if ok else 'FAIL'} | {results[-1].detail}")
    print(f"  answer: {preview(a, 320)}")

    print("\n=== RESUMO ===")
    failed = [r for r in results if not r.ok]
    for r in results:
        print(f"{'PASS' if r.ok else 'FAIL'} {r.name}: {r.detail}")
        print(f"   → {r.answer_preview[:200]}")
    print(f"\n{len(results) - len(failed)}/{len(results)} PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
