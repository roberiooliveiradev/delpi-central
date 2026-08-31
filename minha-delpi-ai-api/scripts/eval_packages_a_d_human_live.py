#!/usr/bin/env python3
"""Roteiro humano A–D — typos, variações e re-checagem das falhas.

Simula usuário real: abreviações, erros de digitação, frases alternativas.
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
from dataclasses import dataclass, field

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
USER = os.environ.get("SMOKE_USER", "rober").strip()
PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

AGENTE_RE = re.compile(r"agente|especialista|ative", re.I)
DADOS_RE = re.compile(r"dados consultados|j[aá] foram consultados", re.I)
ESTOQUE_RE = re.compile(r"estoque do produto", re.I)
BY_BRANCH_RE = re.compile(r"by-branch|por.?filial", re.I)


@dataclass
class Turn:
    label: str
    message: str
    expect: str  # identity_fast | guidance | rol_01 | compare_dual | yoy | branch_dual | data_answer | soft
    use_agent: bool = False
    seed: list[str] = field(default_factory=list)
    status: str = "SKIP"
    detail: str = ""
    prose: str = ""
    ms: int = 0


def _req(method: str, url: str, *, token: str | None = None, body: dict | None = None, timeout: float = 240) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "username": USER,
            "password": PASSWORD,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE}/auth/realms/{REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return str(payload["access_token"])


def _first_agent(token: str) -> str | None:
    agents = _req("GET", f"{BASE}{PREFIX}/agents?limit=40", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if isinstance(agent, dict) and agent.get("enabled") and agent.get("id"):
            return str(agent["id"])
    return None


def _session(token: str, title: str, agent_id: str | None = None) -> str:
    body: dict = {"title": title}
    if agent_id:
        body["agentId"] = agent_id
    payload = _req("POST", f"{BASE}{PREFIX}/sessions", token=token, body=body)
    return str(payload["id"])


def _send(token: str, session_id: str, message: str, agent_id: str | None = None) -> tuple[dict, int]:
    body: dict = {"message": message, "responseMode": "normal", "adminDebug": True}
    if agent_id:
        body["agentId"] = agent_id
    t0 = time.perf_counter()
    try:
        payload = _req(
            "POST",
            f"{BASE}{PREFIX}/sessions/{session_id}/messages",
            token=token,
            body=body,
            timeout=300,
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:400]}") from exc
    ms = int((time.perf_counter() - t0) * 1000)
    msg = payload.get("message") if isinstance(payload.get("message"), dict) else payload
    if isinstance(payload.get("assistantMessage"), dict):
        msg = payload["assistantMessage"]
    return (msg if isinstance(msg, dict) else {"content": str(payload)}), ms


def _prose(msg: dict) -> str:
    return str(msg.get("content") or msg.get("answer") or "").strip()


def _tools(msg: dict) -> list[dict]:
    return [t for t in (msg.get("toolCalls") or []) if isinstance(t, dict)]


def _paths(msg: dict) -> list[str]:
    out = []
    for tc in _tools(msg):
        args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
        path = str(args.get("path") or "").strip()
        meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        path = path or str(meta.get("path") or "").strip()
        if path:
            out.append(path)
    return out


def _branches(msg: dict) -> list[str]:
    out = []
    for tc in _tools(msg):
        args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
        params = args.get("parameters") if isinstance(args.get("parameters"), dict) else {}
        br = params.get("branch")
        if br is not None and str(br).strip():
            out.append(str(br).strip())
    return out


def _roles(msg: dict) -> list[str]:
    out = []
    for tc in _tools(msg):
        if tc.get("periodCompareRole"):
            out.append(str(tc["periodCompareRole"]))
        args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
        diag = args.get("selectionDiagnostics") if isinstance(args.get("selectionDiagnostics"), dict) else {}
        if diag.get("periodCompareRole"):
            out.append(str(diag["periodCompareRole"]))
    return out


def _data_answer_in_tools(msg: dict) -> bool:
    for tc in _tools(msg):
        meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        if meta.get("dataAnswer") or meta.get("dataCommentary"):
            return True
    meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
    return bool(meta.get("dataAnswer") or meta.get("dataCommentary"))


def _admin_pipeline(msg: dict) -> dict:
    admin = msg.get("adminDebug") if isinstance(msg.get("adminDebug"), dict) else {}
    if not admin:
        meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
        admin = meta.get("adminDebug") if isinstance(meta.get("adminDebug"), dict) else {}
    pipeline = admin.get("pipeline") if isinstance(admin.get("pipeline"), dict) else {}
    return {
        "skipRag": pipeline.get("skipRag") or admin.get("skipRag"),
        "stages": admin.get("pipelineStages") or pipeline.get("stages") or admin.get("stages"),
        "stage": admin.get("stage") or pipeline.get("stage"),
    }


def _judge(turn: Turn, msg: dict, ms: int) -> None:
    prose = _prose(msg)
    turn.prose = prose[:280]
    turn.ms = ms
    paths = _paths(msg)
    branches = _branches(msg)
    roles = _roles(msg)
    tools = _tools(msg)
    errors: list[str] = []

    if turn.expect == "identity_fast":
        if not prose:
            errors.append("prosa vazia")
        if DADOS_RE.search(prose):
            errors.append("notice dados consultados")
        if any("execute_external" in str(t.get("name") or "") for t in tools):
            errors.append("tool operacional")
        if ms > 8000:
            errors.append(f"lento {ms}ms (heurística miss?)")
        # content ok even if slow → mark PARTIAL via detail
    elif turn.expect == "guidance":
        if not AGENTE_RE.search(prose):
            errors.append("sem guidance agente")
        if any("/financial/rol" in p for p in paths):
            errors.append("executou ROL no comum")
    elif turn.expect == "rol_01":
        if not any("/financial/rol" in p and "by-branch" not in p for p in paths):
            if any("by-branch" in p for p in paths):
                errors.append("by-branch")
            elif not paths:
                errors.append("sem tool ROL")
        br_norm = {str(b).zfill(2) for b in branches}
        if branches and "02" in br_norm:
            errors.append(f"filial extra {branches}")
        if ESTOQUE_RE.search(prose):
            errors.append("prosa estoque")
    elif turn.expect == "compare_dual":
        execs = sum(1 for t in tools if "execute_external" in str(t.get("name") or ""))
        if execs < 2:
            errors.append(f"sem dual ({execs})")
        if not prose:
            errors.append("prosa vazia")
        if "ano anterior" in prose.lower() and "período anterior" not in prose.lower() and "periodo anterior" not in prose.lower():
            # soft quality note only if previous_period scenario
            if "período anterior" in turn.message.lower() or "periodo anterior" in turn.message.lower():
                errors.append("label prior YoY em previous_period")
    elif turn.expect == "yoy":
        execs = sum(1 for t in tools if "execute_external" in str(t.get("name") or ""))
        if execs < 2 and "2025" not in prose:
            errors.append(f"sem YoY dual ({execs})")
    elif turn.expect == "branch_dual":
        execs = sum(1 for t in tools if "execute_external" in str(t.get("name") or ""))
        br_norm = {str(b).zfill(2) for b in branches}
        if execs < 2:
            errors.append(f"sem dual ({execs})")
        if not ({"01", "02"} <= br_norm):
            errors.append(f"branches={branches}")
        if "o que é" in prose.lower() and "rol" in prose.lower():
            errors.append("pediu definição de ROL")
    elif turn.expect == "data_answer":
        if not tools:
            errors.append("sem tools")
        if tools and not _data_answer_in_tools(msg):
            errors.append("sem dataAnswer em toolCalls.metadata")
        if not prose:
            errors.append("prosa vazia")
    elif turn.expect == "soft":
        if not prose or len(prose) < 8:
            errors.append("resposta vazia")

    pipe = _admin_pipeline(msg)
    detail_bits = []
    if errors:
        turn.status = "FAIL"
        detail_bits.append("; ".join(errors))
    else:
        turn.status = "PASS"
        detail_bits.append("ok")
    detail_bits.append(f"{ms}ms")
    if paths:
        detail_bits.append(f"paths={paths[:4]}")
    if branches:
        detail_bits.append(f"br={branches}")
    if roles:
        detail_bits.append(f"roles={list(dict.fromkeys(roles))}")
    if pipe.get("skipRag") is not None:
        detail_bits.append(f"skipRag={pipe.get('skipRag')}")
    turn.detail = " | ".join(detail_bits)


def _run_turn(token: str, agent_id: str | None, turn: Turn) -> str:
    """Returns possibly refreshed token."""
    print(f"\n→ [{turn.label}] {turn.message!r}", flush=True)
    aid = agent_id if turn.use_agent else None
    try:
        sid = _session(token, f"human-{turn.label}"[:60], agent_id=aid)
    except urllib.error.HTTPError as exc:
        if exc.code != 401:
            turn.status = "FAIL"
            turn.detail = f"HTTP {exc.code} session"
            print(f"  [{turn.status}] {turn.detail}", flush=True)
            return token
        print("  auth refresh…", flush=True)
        token = _token()
        sid = _session(token, f"human-{turn.label}"[:60], agent_id=aid)
    try:
        for seed in turn.seed:
            print(f"  seed: {seed!r}", flush=True)
            try:
                _send(token, sid, seed, agent_id=aid)
            except RuntimeError as exc:
                if "401" not in str(exc):
                    raise
                token = _token()
                _send(token, sid, seed, agent_id=aid)
        msg, ms = _send(token, sid, turn.message, agent_id=aid)
        _judge(turn, msg, ms)
    except Exception as exc:  # noqa: BLE001
        turn.status = "FAIL"
        turn.detail = str(exc)[:320]
    print(f"  [{turn.status}] {turn.detail}", flush=True)
    if turn.prose:
        print(f"  prosa: {turn.prose.replace(chr(10), ' ')[:180]}", flush=True)
    return token


def main() -> int:
    print("auth…", flush=True)
    token = _token()
    agent_id = _first_agent(token)
    print(f"agent={agent_id}", flush=True)

    only = {x.strip() for x in os.environ.get("SMOKE_ONLY", "").split(",") if x.strip()}

    turns: list[Turn] = [
        # --- Falha B: identity / typos ---
        Turn("B1-typo-u", "como u posso te chamar?", "identity_fast"),
        Turn("B2-typo-vc", "como vc se chama?", "identity_fast"),
        Turn("B3-typo-chamo", "como te chamo mesmo?", "identity_fast"),
        Turn("B4-canon", "como posso te chamar?", "identity_fast"),
        Turn("B5-nome", "qual seu nome?", "identity_fast"),
        # --- Pass A: guidance variações ---
        Turn("A1-rol-comum", "qual o rol filial 01", "guidance"),
        Turn("A2-typo-filail", "me fala o rol da filail 01", "guidance"),
        Turn("A3-abreviado", "rol 01 agora", "guidance"),
        Turn("A4-faturamento", "quanto foi o faturamento da filial 01?", "guidance"),
        # --- Pass A: ROL agent variações ---
        Turn("A5-rol-agente", "ROL filial 01 agosto 2026", "rol_01", use_agent=True),
        Turn("A6-typo-filail-ag", "rol da filail 01 em agosto/2026", "rol_01", use_agent=True),
        Turn("A7-abreviado-ag", "rol 01 ago/26", "rol_01", use_agent=True),
        Turn("A8-por-extenso", "me mostra o ROL só da unidade 01 no mês de agosto de 2026", "rol_01", use_agent=True),
        # --- Falha C: dataAnswer ---
        Turn("C1-consolidado", "qual o rol consolidado em agosto 2026", "data_answer", use_agent=True),
        Turn("C2-typo", "rol consollidado ago 2026", "data_answer", use_agent=True),
        # --- Pass D: previous_period variações ---
        Turn(
            "D1-periodo-ant",
            "comparar com o período anterior",
            "compare_dual",
            use_agent=True,
            seed=["ROL filial 01 agosto 2026"],
        ),
        Turn(
            "D2-typo-periodo",
            "compara com o periodo anteriror",
            "compare_dual",
            use_agent=True,
            seed=["ROL filial 01 agosto 2026"],
        ),
        Turn(
            "D3-mes-passado",
            "e no mês passado?",
            "soft",
            use_agent=True,
            seed=["ROL filial 01 agosto 2026"],
        ),
        # --- Falha D: branch compare ---
        Turn(
            "D4-filiais",
            "comparar filial 01 com filial 02",
            "branch_dual",
            use_agent=True,
            seed=["ROL agosto 2026"],
        ),
        Turn(
            "D5-typo-filiais",
            "compara filail 01 vs filail 02",
            "branch_dual",
            use_agent=True,
            seed=["ROL filial 01 agosto 2026"],
        ),
        Turn(
            "D6-entre-filiais",
            "compara entre filiais 01 e 02",
            "branch_dual",
            use_agent=True,
            seed=["ROL agosto 2026"],
        ),
        # --- Herança YoY ---
        Turn(
            "Y1-yoy",
            "comparar com ano anterior no mesmo periodo",
            "yoy",
            use_agent=True,
            seed=["ROL filial 01 agosto 2026"],
        ),
        Turn(
            "Y2-typo-yoy",
            "compara c ano anteriror mesmo periodo",
            "yoy",
            use_agent=True,
            seed=["ROL filial 01 agosto 2026"],
        ),
        Turn(
            "Y3-challenge",
            "mas a filial 01 não é o consolidado né?",
            "soft",
            use_agent=True,
            seed=["ROL agosto 2026", "somente da filial 01"],
        ),
    ]

    if only:
        turns = [t for t in turns if t.label in only]

    for turn in turns:
        token = _run_turn(token, agent_id, turn)

    print("\n=== RESUMO HUMANO ===")
    passed = failed = 0
    for t in turns:
        print(f"{t.status}\t{t.label}\t{t.detail}")
        if t.status == "PASS":
            passed += 1
        else:
            failed += 1
    print(f"\nTOTAL PASS={passed} FAIL={failed}")

    out = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "docs", "operations", "smoke-packages-a-d-human-eval.json")
    )
    # merge with previous partial if SMOKE_ONLY
    existing: list[dict] = []
    if only and os.path.exists(out):
        try:
            with open(out, encoding="utf-8") as fh:
                existing = json.load(fh)
        except Exception:
            existing = []
    fresh = [
        {
            "label": t.label,
            "message": t.message,
            "expect": t.expect,
            "status": t.status,
            "detail": t.detail,
            "ms": t.ms,
            "prose": t.prose,
            "seed": t.seed,
            "use_agent": t.use_agent,
        }
        for t in turns
    ]
    if existing:
        by_label = {row["label"]: row for row in existing if isinstance(row, dict)}
        for row in fresh:
            by_label[row["label"]] = row
        payload = list(by_label.values())
    else:
        payload = fresh
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"wrote {out}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
