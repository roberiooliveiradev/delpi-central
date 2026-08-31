#!/usr/bin/env python3
"""Avaliação live A–D — critérios do plano compare_grounded_p0."""

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

DADOS_CONSULTADOS = re.compile(r"dados consultados|j[aá] foram consultados", re.I)
ESTOQUE_TITLE = re.compile(r"estoque do produto", re.I)
AGENTE_GUIDANCE = re.compile(r"agente|especialista|ative", re.I)
BARS_CLAIM = re.compile(r"gr[aá]fico de barras|barras", re.I)


@dataclass
class EvalRow:
    criterion: str
    package: str
    message: str
    status: str = "FAIL"
    detail: str = ""
    prose: str = ""
    elapsed_ms: int = 0
    extras: dict = field(default_factory=dict)


def _req(method: str, url: str, *, token: str | None = None, body: dict | None = None, timeout: float = 180) -> dict:
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
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"token ausente: {payload}")
    return str(token)


def _session(token: str, title: str, agent_id: str | None = None) -> str:
    body: dict = {"title": title}
    if agent_id:
        body["agentId"] = agent_id
    payload = _req("POST", f"{BASE}{PREFIX}/sessions", token=token, body=body)
    sid = payload.get("id")
    if not sid:
        raise RuntimeError(f"sessão inválida: {payload}")
    return str(sid)


def _send(token: str, session_id: str, message: str, agent_id: str | None = None) -> tuple[dict, int]:
    body: dict = {"message": message, "responseMode": "normal"}
    if agent_id:
        body["agentId"] = agent_id
    t0 = time.perf_counter()
    try:
        payload = _req(
            "POST",
            f"{BASE}{PREFIX}/sessions/{session_id}/messages",
            token=token,
            body=body,
            timeout=240,
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:500]}") from exc
    elapsed = int((time.perf_counter() - t0) * 1000)
    # envelope: { message: {...} } or assistant at root
    msg = payload.get("message") if isinstance(payload.get("message"), dict) else payload
    if isinstance(payload.get("assistantMessage"), dict):
        msg = payload["assistantMessage"]
    return msg if isinstance(msg, dict) else {"content": str(payload)}, elapsed


def _prose(msg: dict) -> str:
    return str(msg.get("content") or msg.get("answer") or "").strip()


def _admin(msg: dict) -> dict:
    meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
    admin = msg.get("adminDebug") if isinstance(msg.get("adminDebug"), dict) else {}
    if not admin and isinstance(meta.get("adminDebug"), dict):
        admin = meta["adminDebug"]
    return admin


def _tool_paths(msg: dict) -> list[str]:
    paths: list[str] = []
    for tc in msg.get("toolCalls") or []:
        if not isinstance(tc, dict):
            continue
        args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
        path = str(args.get("path") or tc.get("path") or "").strip()
        if not path:
            meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
            path = str(meta.get("path") or "").strip()
        if path:
            paths.append(path)
        # also nested selection
        for key in ("parameters",):
            params = args.get(key) if isinstance(args.get(key), dict) else {}
            br = params.get("branch")
            if br is not None:
                paths.append(f"branch={br}")
    return paths


def _branches(msg: dict) -> list[str]:
    out: list[str] = []
    for tc in msg.get("toolCalls") or []:
        if not isinstance(tc, dict):
            continue
        args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
        params = args.get("parameters") if isinstance(args.get("parameters"), dict) else {}
        br = params.get("branch")
        if br is not None and str(br).strip():
            out.append(str(br).strip())
    return out


def _data_answer(msg: dict) -> bool:
    meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
    return bool(meta.get("dataAnswer") or meta.get("dataCommentary"))


def _selected(msg: dict) -> str:
    meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
    decision = meta.get("presentationDecision") if isinstance(meta.get("presentationDecision"), dict) else {}
    return str(decision.get("selected") or "").strip()


def _title(msg: dict) -> str:
    meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
    for key in ("itemsTitle", "tableTitle", "presentationTitle"):
        if meta.get(key):
            return str(meta.get(key))
    tables = meta.get("operationalTables") if isinstance(meta.get("operationalTables"), list) else []
    if tables and isinstance(tables[0], dict) and tables[0].get("title"):
        return str(tables[0]["title"])
    kpi = meta.get("kpiPresentation") if isinstance(meta.get("kpiPresentation"), dict) else {}
    if kpi.get("title"):
        return str(kpi["title"])
    return ""


def _first_agent(token: str) -> str | None:
    agents = _req("GET", f"{BASE}{PREFIX}/agents?limit=40", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if not isinstance(agent, dict):
            continue
        if agent.get("enabled") and agent.get("visibility") in {"system", "official", None}:
            name = str(agent.get("name") or "").lower()
            # prefer financial / operational sounding
            if any(k in name for k in ("financ", "operac", "kpi", "delpi")):
                return str(agent["id"])
    for agent in items:
        if isinstance(agent, dict) and agent.get("enabled") and agent.get("id"):
            return str(agent["id"])
    return None


def main() -> int:
    print("auth…", flush=True)
    token = _token()
    agent_id = _first_agent(token)
    print(f"agent={agent_id}", flush=True)
    rows: list[EvalRow] = []

    # 1 B — typo identity
    row = EvalRow("1 Typo identity rápido sem notice dados", "B", "como u posso te chamar?")
    try:
        sid = _session(token, "eval-B-identity")
        msg, ms = _send(token, sid, row.message)
        prose = _prose(msg)
        admin = _admin(msg)
        tools = msg.get("toolCalls") or []
        row.elapsed_ms = ms
        row.prose = prose[:240]
        row.extras = {
            "tools": len(tools),
            "stage": admin.get("stage") or admin.get("pipelineStage"),
            "skipRag": admin.get("skipRag") or admin.get("skip_rag"),
        }
        errors = []
        if not prose:
            errors.append("prosa vazia")
        if DADOS_CONSULTADOS.search(prose):
            errors.append("notice dados consultados")
        if ms > 12000:
            errors.append(f"lento {ms}ms")
        if len(tools) > 0 and any(
            "execute_external" in str(t.get("name") or "") for t in tools if isinstance(t, dict)
        ):
            errors.append("tool operacional inesperado")
        row.status = "PASS" if not errors else "FAIL"
        row.detail = "; ".join(errors) or f"ok {ms}ms tools={len(tools)}"
    except Exception as exc:  # noqa: BLE001
        row.detail = str(exc)[:300]
    rows.append(row)
    print(f"[{row.status}] {row.criterion}: {row.detail}", flush=True)

    # 2 A — common chat ROL → guidance
    row = EvalRow("2 Comum operacional → guidance agente", "A", "qual o rol filial 01")
    try:
        sid = _session(token, "eval-A-common")
        msg, ms = _send(token, sid, row.message)
        prose = _prose(msg)
        row.elapsed_ms = ms
        row.prose = prose[:240]
        paths = _tool_paths(msg)
        errors = []
        if not AGENTE_GUIDANCE.search(prose):
            errors.append("sem orientação de agente")
        if any("/financial/rol" in p for p in paths):
            errors.append("executou ROL no comum")
        row.status = "PASS" if not errors else "FAIL"
        row.detail = "; ".join(errors) or f"guidance ok; paths={paths}"
    except Exception as exc:  # noqa: BLE001
        row.detail = str(exc)[:300]
    rows.append(row)
    print(f"[{row.status}] {row.criterion}: {row.detail}", flush=True)

    # 2b A — resume period with pending (guidance, not empty LLM)
    row = EvalRow("2b Resume período → guidance/continuidade", "A", "agosto de 2026")
    try:
        sid = _session(token, "eval-A-resume")
        # seed pending via first operational ask in common
        _send(token, sid, "qual o rol")
        msg, ms = _send(token, sid, row.message)
        prose = _prose(msg)
        row.elapsed_ms = ms
        row.prose = prose[:240]
        errors = []
        if not prose or len(prose) < 12:
            errors.append("resposta vazia/curta demais")
        # empty LLM hallucination markers
        if prose.strip().lower() in {"ok", "certo", "entendi"}:
            errors.append("LLM vazio genérico")
        row.status = "PASS" if not errors else "FAIL"
        row.detail = "; ".join(errors) or "resposta presente"
    except Exception as exc:  # noqa: BLE001
        row.detail = str(exc)[:300]
    rows.append(row)
    print(f"[{row.status}] {row.criterion}: {row.detail}", flush=True)

    # 3 A — agent ROL filial 01 scalar + title/prose
    row = EvalRow("3 Agente ROL filial 01 só 01; título/prosa", "A", "ROL filial 01 agosto 2026")
    try:
        if not agent_id:
            raise RuntimeError("sem agente")
        sid = _session(token, "eval-A-rol-agent", agent_id=agent_id)
        msg, ms = _send(token, sid, row.message, agent_id=agent_id)
        prose = _prose(msg)
        paths = _tool_paths(msg)
        branches = _branches(msg)
        title = _title(msg)
        selected = _selected(msg)
        row.elapsed_ms = ms
        row.prose = prose[:240]
        row.extras = {"paths": paths, "branches": branches, "title": title, "selected": selected}
        errors = []
        if any("by-branch" in p for p in paths):
            errors.append("usou by-branch")
        if branches and not all(b in {"01", "1"} or str(b).zfill(2) == "01" for b in branches):
            # allow only 01
            if any(str(b).zfill(2) not in {"01", "al"} and str(b) not in {"01", "all"} for b in branches):
                if any(str(b).zfill(2) == "02" for b in branches):
                    errors.append(f"filiais extras {branches}")
        if ESTOQUE_TITLE.search(title) or ESTOQUE_TITLE.search(prose):
            errors.append("título/prosa de estoque")
        if selected == "table" and BARS_CLAIM.search(prose):
            errors.append("prosa cita barras com selected=table")
        if not paths and not prose:
            errors.append("sem tool e sem prosa")
        row.status = "PASS" if not errors else "FAIL"
        row.detail = "; ".join(errors) or f"paths={paths} branches={branches} title={title!r} selected={selected}"
    except Exception as exc:  # noqa: BLE001
        row.detail = str(exc)[:300]
    rows.append(row)
    print(f"[{row.status}] {row.criterion}: {row.detail}", flush=True)

    # 4 C — dataAnswer / context (agent operational)
    row = EvalRow("4 Prompt contexto; dataAnswer; síntese", "C", "qual o rol consolidado em agosto 2026")
    try:
        if not agent_id:
            raise RuntimeError("sem agente")
        sid = _session(token, "eval-C-dataanswer", agent_id=agent_id)
        msg, ms = _send(token, sid, row.message, agent_id=agent_id)
        prose = _prose(msg)
        has_da = _data_answer(msg)
        admin = _admin(msg)
        row.elapsed_ms = ms
        row.prose = prose[:240]
        row.extras = {"dataAnswer": has_da, "selected": _selected(msg)}
        errors = []
        if not prose:
            errors.append("prosa vazia")
        if not has_da and not _tool_paths(msg):
            errors.append("sem dataAnswer e sem tools")
        # soft: dataAnswer preferred when tools ran
        if _tool_paths(msg) and not has_da:
            errors.append("tools sem dataAnswer/dataCommentary")
        row.status = "PASS" if not errors else "FAIL"
        row.detail = "; ".join(errors) or f"dataAnswer={has_da} selected={_selected(msg)}"
    except Exception as exc:  # noqa: BLE001
        row.detail = str(exc)[:300]
    rows.append(row)
    print(f"[{row.status}] {row.criterion}: {row.detail}", flush=True)

    # 5 D — previous_period dual (after baseline ROL)
    row = EvalRow("5 previous_period dual", "D", "comparar com o período anterior")
    try:
        if not agent_id:
            raise RuntimeError("sem agente")
        sid = _session(token, "eval-D-prev", agent_id=agent_id)
        _send(token, sid, "ROL filial 01 agosto 2026", agent_id=agent_id)
        msg, ms = _send(token, sid, row.message, agent_id=agent_id)
        prose = _prose(msg)
        paths = _tool_paths(msg)
        roles = []
        for tc in msg.get("toolCalls") or []:
            if isinstance(tc, dict) and tc.get("periodCompareRole"):
                roles.append(tc["periodCompareRole"])
            args = tc.get("arguments") if isinstance(tc, dict) and isinstance(tc.get("arguments"), dict) else {}
            diag = args.get("selectionDiagnostics") if isinstance(args.get("selectionDiagnostics"), dict) else {}
            if diag.get("periodCompareRole"):
                roles.append(diag["periodCompareRole"])
        row.elapsed_ms = ms
        row.prose = prose[:240]
        row.extras = {"paths": paths, "roles": roles}
        errors = []
        if not prose:
            errors.append("prosa vazia")
        # dual preferred
        exec_count = sum(
            1
            for tc in (msg.get("toolCalls") or [])
            if isinstance(tc, dict) and "execute_external" in str(tc.get("name") or "")
        )
        if exec_count < 2 and "compar" not in prose.lower() and "varia" not in prose.lower():
            errors.append(f"sem dual ({exec_count} tools) e prosa sem comparação")
        row.status = "PASS" if not errors else "FAIL"
        row.detail = "; ".join(errors) or f"tools={exec_count} roles={roles}"
    except Exception as exc:  # noqa: BLE001
        row.detail = str(exc)[:300]
    rows.append(row)
    print(f"[{row.status}] {row.criterion}: {row.detail}", flush=True)

    # 5b D — branch compare
    row = EvalRow("5b filial×filial dual", "D", "comparar filial 01 com filial 02")
    try:
        if not agent_id:
            raise RuntimeError("sem agente")
        sid = _session(token, "eval-D-branch", agent_id=agent_id)
        _send(token, sid, "ROL agosto 2026", agent_id=agent_id)
        msg, ms = _send(token, sid, row.message, agent_id=agent_id)
        prose = _prose(msg)
        branches = _branches(msg)
        row.elapsed_ms = ms
        row.prose = prose[:240]
        row.extras = {"branches": branches}
        errors = []
        if not prose:
            errors.append("prosa vazia")
        br_norm = {str(b).zfill(2) for b in branches}
        if branches and not ({"01", "02"} <= br_norm or br_norm == {"01", "02"}):
            # still ok if prose mentions both
            if not ("01" in prose and "02" in prose):
                errors.append(f"filiais {branches}")
        row.status = "PASS" if not errors else "FAIL"
        row.detail = "; ".join(errors) or f"branches={branches}"
    except Exception as exc:  # noqa: BLE001
        row.detail = str(exc)[:300]
    rows.append(row)
    print(f"[{row.status}] {row.criterion}: {row.detail}", flush=True)

    # 6 inheritance YoY
    row = EvalRow("6 YoY sem regressão", "herança", "comparar com ano anterior no mesmo periodo")
    try:
        if not agent_id:
            raise RuntimeError("sem agente")
        sid = _session(token, "eval-YoY", agent_id=agent_id)
        _send(token, sid, "ROL filial 01 agosto 2026", agent_id=agent_id)
        msg, ms = _send(token, sid, row.message, agent_id=agent_id)
        prose = _prose(msg)
        exec_count = sum(
            1
            for tc in (msg.get("toolCalls") or [])
            if isinstance(tc, dict) and "execute_external" in str(tc.get("name") or "")
        )
        row.elapsed_ms = ms
        row.prose = prose[:240]
        errors = []
        if not prose:
            errors.append("prosa vazia")
        if exec_count < 1 and "ano" not in prose.lower():
            errors.append("sem reexecução/comparação")
        row.status = "PASS" if not errors else "FAIL"
        row.detail = "; ".join(errors) or f"tools={exec_count}"
    except Exception as exc:  # noqa: BLE001
        row.detail = str(exc)[:300]
    rows.append(row)
    print(f"[{row.status}] {row.criterion}: {row.detail}", flush=True)

    print("\n=== RESUMO ===")
    for r in rows:
        print(f"{r.status}\t{r.package}\t{r.criterion}\t{r.detail}")
        if r.prose:
            print(f"  prosa: {r.prose.replace(chr(10), ' ')[:160]}")

    out_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "docs",
        "operations",
        "smoke-packages-a-d-live-evaluation.json",
    )
    out_path = os.path.abspath(out_path)
    payload = [
        {
            "criterion": r.criterion,
            "package": r.package,
            "message": r.message,
            "status": r.status,
            "detail": r.detail,
            "elapsed_ms": r.elapsed_ms,
            "prose": r.prose,
            "extras": r.extras,
        }
        for r in rows
    ]
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"\nwrote {out_path}")
    return 0 if all(r.status == "PASS" for r in rows) else 1


if __name__ == "__main__":
    # wait API
    for i in range(30):
        try:
            urllib.request.urlopen(f"{BASE}/apps/minha-delpi-ai/api/health", timeout=3)
            break
        except Exception:
            try:
                urllib.request.urlopen(f"{BASE}{PREFIX.replace('/chat','')}/health", timeout=3)
                break
            except Exception:
                time.sleep(2)
    else:
        print("API não respondeu health; tentando mesmo assim…", flush=True)
    sys.exit(main())
