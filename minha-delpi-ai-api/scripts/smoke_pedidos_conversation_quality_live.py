#!/usr/bin/env python3
"""Live — qualidade em UMA conversa sobre pedidos (perguntas longas + follow-ups).

Uso:
  cd minha-delpi-ai-api
  PYTHONPATH=. .venv/bin/python -u scripts/smoke_pedidos_conversation_quality_live.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip() or "http://localhost"
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USER = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_PAUSE = float(os.environ.get("SMOKE_CASE_PAUSE", "3.5"))


TURNS: list[dict[str, str]] = [
    {
        "id": "T1-carteira-longa",
        "message": (
            "Preciso entender a carteira de pedidos de venda em aberto do produto "
            "90262910: liste os pedidos abertos com cliente, quantidade e datas "
            "quando existirem, e diga se a concentração está mais na filial 01 ou 02. "
            "Quero uma leitura útil para atendimento, não só dump de campos técnicos."
        ),
    },
    {
        "id": "T2-filial-follow",
        "message": "e somente da filial 01, por favor?",
    },
    {
        "id": "T3-atraso-otd-longo",
        "message": (
            "Considerando esses pedidos que estamos falando: quais estão mais "
            "atrasados em relação à data de entrega prometida, o que isso implica "
            "para OTD/atraso, e se não tiver indicador OTD desse produto me diga "
            "explicitamente o que falta em vez de inventar."
        ),
    },
    {
        "id": "T4-ordinal",
        "message": "detalha o segundo da lista pra mim",
    },
    {
        "id": "T5-estoque-cobertura",
        "message": (
            "Além disso, me fala o estoque atual desse mesmo produto e se a "
            "disponibilidade cobre a soma das quantidades em aberto que você "
            "listou nesta conversa. Se não der para somar com precisão, explique "
            "o limite dos dados."
        ),
    },
    {
        "id": "T6-fornecedores",
        "message": "e quais são os fornecedores desse item?",
    },
    {
        "id": "T7-resumo-executivo",
        "message": (
            "Fecha com um resumo executivo do que vimos nesta conversa sobre "
            "pedidos, estoque e risco de atendimento — no máximo 8 linhas, "
            "sem repetir tabela inteira nem jargão de API."
        ),
    },
]


def _token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USER,
            "password": _PASSWORD,
        }
    ).encode()
    req = urllib.request.Request(
        f"{_BASE}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"token ausente: {payload}")
    return str(token)


def _request(
    method: str,
    url: str,
    *,
    auth: dict[str, str],
    body: dict | None = None,
    timeout: int = 360,
) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    refreshed = False
    for attempt in range(8):
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {auth['token']}",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and not refreshed:
                print("  (401 — renovando token)", flush=True)
                auth["token"] = _token()
                refreshed = True
                continue
            if exc.code == 429:
                sleep_s = min(65.0, 8.0 * (2**attempt))
                print(f"  (429 — retry em {sleep_s:.0f}s)", flush=True)
                time.sleep(sleep_s)
                continue
            raise
    raise RuntimeError(f"falha HTTP persistente: {method} {url}")


def _first_agent(auth: dict[str, str]) -> str:
    agents = _request("GET", f"{_BASE}{_CHAT}/agents?limit=40", auth=auth)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and "delpi" in str(agent.get("name") or "").lower():
            return str(agent["id"])
    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])
    raise RuntimeError("nenhum agente")


def _unwrap(payload: dict) -> dict:
    if isinstance(payload.get("assistantMessage"), dict):
        return payload["assistantMessage"]
    if isinstance(payload.get("message"), dict):
        return payload["message"]
    return payload


def _admin(msg: dict) -> dict:
    debug = msg.get("adminDebug")
    if isinstance(debug, dict):
        return debug
    meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
    nested = meta.get("adminDebug") if isinstance(meta.get("adminDebug"), dict) else {}
    return nested if isinstance(nested, dict) else {}


def _tools(msg: dict) -> list[dict]:
    calls = msg.get("toolCalls")
    if isinstance(calls, list) and calls:
        return [t for t in calls if isinstance(t, dict)]
    admin = _admin(msg)
    tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
    nested = tooling.get("toolCalls")
    if isinstance(nested, list):
        return [t for t in nested if isinstance(t, dict)]
    return []


def _paths(msg: dict) -> list[str]:
    out: list[str] = []
    for tool in _tools(msg):
        meta = tool.get("metadata") if isinstance(tool.get("metadata"), dict) else {}
        path = str(meta.get("path") or tool.get("path") or "").strip()
        if path:
            out.append(path)
    return out


def _ops(msg: dict) -> list[str]:
    out: list[str] = []
    for tool in _tools(msg):
        meta = tool.get("metadata") if isinstance(tool.get("metadata"), dict) else {}
        op = str(meta.get("operationId") or "").strip()
        if op:
            out.append(op)
    return out


def _prose(msg: dict) -> str:
    return str(msg.get("content") or msg.get("answer") or "").strip()


def _quality_notes(turn_id: str, prose: str, paths: list[str]) -> list[str]:
    notes: list[str] = []
    low = prose.lower()
    if not prose:
        notes.append("FAIL prosa vazia")
        return notes
    if len(prose) < 40:
        notes.append("WARN prosa muito curta")
    # jargão cru típico de template ruim
    for bad in ("last_price", "planned_qty", "open_orders_count", "page_size"):
        if bad in low:
            notes.append(f"WARN jargão técnico na prosa: {bad}")
    if "<!-- section:" in low:
        notes.append("WARN markup interno vazou na prosa")
    if turn_id.startswith("T1") and not any(
        "open-order" in p or "pedido" in p or "/sales/open-orders" in p for p in paths
    ):
        if not any("order" in p for p in paths):
            notes.append("WARN T1 sem path de pedidos/carteira")
    if turn_id.startswith("T2") and "01" not in prose and "filial" not in low:
        notes.append("WARN T2 pode não ter ancorado filial 01")
    if turn_id.startswith("T4") and any(
        x in low for x in ("não sei", "não tenho lista", "informe o código")
    ):
        notes.append("WARN T4 perdeu referência ordinal da lista")
    if turn_id.startswith("T5") and not any("stock" in p for p in paths):
        notes.append("WARN T5 sem path de estoque")
    if turn_id.startswith("T6") and not any("supplier" in p for p in paths):
        notes.append("WARN T6 sem path de fornecedores")
    if turn_id.startswith("T7"):
        lines = [ln for ln in prose.splitlines() if ln.strip()]
        if len(lines) > 14:
            notes.append(f"WARN T7 verboso demais ({len(lines)} linhas)")
        if "execute_external_action" in low or "/products/" in low:
            notes.append("WARN T7 vazou path/API")
    if not notes:
        notes.append("OK heurística básica")
    return notes


def main() -> int:
    print(f"base={_BASE}", flush=True)
    auth = {"token": _token()}
    agent_id = _first_agent(auth)
    print(f"agent={agent_id}", flush=True)

    session = _request(
        "POST",
        f"{_BASE}{_CHAT}/sessions",
        auth=auth,
        body={"title": "qualidade-pedidos-multiturn", "agentId": agent_id},
    )
    sid = str(session["id"])
    print(f"session={sid}", flush=True)

    results: list[dict[str, Any]] = []
    for index, turn in enumerate(TURNS):
        if index and _PAUSE > 0:
            time.sleep(_PAUSE)
        print(f"\n→ [{turn['id']}] {turn['message'][:100]}…", flush=True)
        t0 = time.perf_counter()
        payload = _request(
            "POST",
            f"{_BASE}{_CHAT}/sessions/{sid}/messages",
            auth=auth,
            body={
                "message": turn["message"],
                "agentId": agent_id,
                "responseMode": "normal",
                "includeAdminDebug": True,
            },
        )
        ms = int((time.perf_counter() - t0) * 1000)
        msg = _unwrap(payload)
        prose = _prose(msg)
        paths = _paths(msg)
        ops = _ops(msg)
        notes = _quality_notes(turn["id"], prose, paths)
        admin = _admin(msg)
        intel = admin.get("intelligence") if isinstance(admin.get("intelligence"), dict) else {}
        row = {
            "turnId": turn["id"],
            "message": turn["message"],
            "ms": ms,
            "paths": paths,
            "operationIds": ops,
            "prose": prose,
            "qualityNotes": notes,
            "clarificationDecision": intel.get("clarificationDecision"),
            "turnUnderstanding": intel.get("turnUnderstanding"),
            "activeTaskPlan": intel.get("activeTaskPlan"),
        }
        results.append(row)
        print(f"  ms={ms} paths={paths} ops={ops}", flush=True)
        print(f"  notes={notes}", flush=True)
        print(f"  prosa: {prose.replace(chr(10), ' ')[:280]}", flush=True)

    out = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "docs",
            "testing",
            "evidence",
            "chat-pedidos-conversation-quality.json",
        )
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(
            {"sessionId": sid, "agentId": agent_id, "turns": results},
            fh,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\nwrote {out}", flush=True)

    warns = sum(1 for r in results for n in r["qualityNotes"] if n.startswith("WARN"))
    fails = sum(1 for r in results for n in r["qualityNotes"] if n.startswith("FAIL"))
    print(f"SUMMARY turns={len(results)} WARN={warns} FAIL={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
