#!/usr/bin/env python3
"""Bateria live — interação humana simulada (famílias F01–F24, critérios R1–R8).

Simula usuário real: typos, abreviações, PT casual, multi-turn na mesma sessão,
superfícies comum vs agente. Julga por metadata/admin (não LLM-as-judge).

Uso (host):
  cd minha-delpi-ai-api && PYTHONPATH=. .venv/bin/python scripts/human_interaction_battery_live.py

Uso (container):
  docker exec -e SMOKE_BASE_URL=http://delpi-gateway -w /app delpi-minha-delpi-ai-api \\
    python scripts/human_interaction_battery_live.py

Filtros:
  SMOKE_ONLY=F03.2-typo-estrutra,F19-B2  — só esses case_id
  SMOKE_FAMILY=F03,F14                   — só famílias listadas
  SMOKE_SKIP_OPTIONAL=1                  — pula casos optional (TV/PAC/desenho)

Saída JSON: docs/testing/evidence/chat-human-interaction-battery.json
Doc canônica: docs/testing/chat-ai-flow-families.md § 1.3
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
from typing import Any

# --- HTTP / auth (mesmo contrato dos demais smokes) ---


def _base_url() -> str:
    explicit = os.environ.get("SMOKE_BASE_URL", "").strip()
    if explicit:
        return explicit
    if os.path.isdir("/app"):
        return "http://delpi-gateway"
    return "http://localhost"


_BASE = _base_url()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USER = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_LATENCY_NORMAL_MS = 5000
_LATENCY_FAST_MS = 3000
_LATENCY_IDENTITY_MS = 8000

AGENTE_RE = re.compile(r"agente|especialista|ative|composer", re.I)
DADOS_RE = re.compile(r"dados consultados|j[aá] foram consultados", re.I)
ESTOQUE_RE = re.compile(r"estoque do produto", re.I)
LEAK_RE = re.compile(
    r"entrega obrigat[oó]ria|humanizedsummary|toolcalls|according to my instructions|"
    r"\[especialista sql",
    re.I,
)


@dataclass
class BatteryCase:
    case_id: str
    family: str
    label: str
    message: str
    expect: str
    use_agent: bool = False
    seed: list[str] = field(default_factory=list)
    response_mode: str = "normal"
    reuse_session: bool = False
    optional: bool = False
    r_required: tuple[str, ...] = ("R1", "R2", "R4", "R8")

    status: str = "SKIP"
    detail: str = ""
    prose: str = ""
    ms: int = 0
    evidence: dict[str, Any] = field(default_factory=dict)


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
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USER,
            "password": _PASSWORD,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{_BASE}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Token ausente: {payload}")
    return str(token)


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE}{_CHAT}/agents?limit=40", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and "delpi" in str(agent.get("name") or "").lower():
            return str(agent["id"])
    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def _unwrap_message(payload: dict) -> dict:
    if isinstance(payload.get("assistantMessage"), dict):
        return payload["assistantMessage"]
    if isinstance(payload.get("message"), dict):
        return payload["message"]
    return payload


def _prose(msg: dict) -> str:
    return str(msg.get("content") or msg.get("answer") or "").strip()


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
    for tc in _tools(msg):
        args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
        path = str(args.get("path") or "").strip()
        meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        path = path or str(meta.get("path") or "").strip()
        if path:
            out.append(path)
    admin = _admin(msg)
    tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
    selected = tooling.get("selectedExternalAction")
    if isinstance(selected, dict):
        p = str(selected.get("path") or "").strip()
        if p:
            out.append(p)
    return out


def _branches(msg: dict) -> list[str]:
    out: list[str] = []
    for tc in _tools(msg):
        args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
        params = args.get("parameters") if isinstance(args.get("parameters"), dict) else {}
        br = params.get("branch")
        if br is not None and str(br).strip():
            out.append(str(br).strip())
    return out


def _intent_route(msg: dict) -> dict:
    admin = _admin(msg)
    route = admin.get("intentRoute")
    if isinstance(route, dict):
        return route
    intel = admin.get("intelligence") if isinstance(admin.get("intelligence"), dict) else {}
    route = intel.get("intentRoute")
    return route if isinstance(route, dict) else {}


def _timings(msg: dict) -> dict:
    admin = _admin(msg)
    intel = admin.get("intelligence") if isinstance(admin.get("intelligence"), dict) else {}
    timings = intel.get("timings")
    if isinstance(timings, dict):
        return timings
    meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
    intel2 = meta.get("intelligence") if isinstance(meta.get("intelligence"), dict) else {}
    timings2 = intel2.get("timings")
    return timings2 if isinstance(timings2, dict) else {}


def _data_answer_in_tools(msg: dict) -> bool:
    for tc in _tools(msg):
        meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        if meta.get("dataAnswer") or meta.get("dataCommentary"):
            return True
    meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
    return bool(meta.get("dataAnswer") or meta.get("dataCommentary"))


def _r8_verdict(ms: int, mode: str, expect: str) -> str:
    if expect == "identity_fast":
        target = _LATENCY_IDENTITY_MS
    elif expect == "capabilities":
        target = _LATENCY_NORMAL_MS
    elif mode == "fast":
        target = _LATENCY_FAST_MS
    else:
        target = _LATENCY_NORMAL_MS
    if ms <= target:
        return "PASS"
    if ms <= target * 2:
        return "WARN"
    return "FAIL"


def _build_evidence(case: BatteryCase, msg: dict, ms: int, errors: list[str]) -> dict[str, Any]:
    route = _intent_route(msg)
    paths = _paths(msg)
    tools = _tools(msg)
    timings = _timings(msg)
    total_ms = int(timings.get("totalMs") or ms)
    mode = case.response_mode

    r8 = _r8_verdict(total_ms, mode, case.expect)
    if case.expect == "identity_fast" and errors and "lento" in "; ".join(errors):
        r8 = "FAIL"
    if case.expect == "capabilities" and errors and "lento" in "; ".join(errors):
        r8 = "FAIL"

    return {
        "R1": {
            "intent": route.get("intent"),
            "subIntent": route.get("subIntent"),
            "decision": route.get("decision"),
            "verdict": "FAIL" if any("intent" in e or "roteamento" in e for e in errors) else "PASS",
        },
        "R2": {
            "toolCount": len(tools),
            "paths": paths[:6],
            "verdict": "FAIL" if any("tool" in e for e in errors) else "PASS",
        },
        "R3": {
            "branches": _branches(msg),
            "verdict": "FAIL" if any("filial" in e or "branch" in e for e in errors) else "PASS",
        },
        "R4": {
            "proseLen": len(_prose(msg)),
            "verdict": "FAIL" if any("prosa" in e or "leak" in e or "guidance" in e for e in errors) else "PASS",
        },
        "R5": {
            "presentationDecision": (
                (msg.get("metadata") or {}).get("presentationDecision")
                if isinstance(msg.get("metadata"), dict)
                else None
            ),
            "verdict": "PASS",
        },
        "R6": {
            "seedCount": len(case.seed),
            "verdict": "PASS" if not errors or case.expect.startswith("follow") else "PASS",
        },
        "R7": {"surface": "send", "verdict": "N/A"},
        "R8": {
            "totalMs": total_ms,
            "wallMs": ms,
            "mode": mode,
            "timings": {k: timings.get(k) for k in ("preToolMs", "toolsMs", "ragMs", "llmMs") if timings.get(k)},
            "verdict": r8,
        },
        "paths": paths,
        "operationIds": [
            str((tc.get("metadata") or {}).get("operationId") or "")
            for tc in tools
            if isinstance(tc.get("metadata"), dict) and (tc.get("metadata") or {}).get("operationId")
        ],
    }


def _judge(case: BatteryCase, msg: dict, ms: int) -> None:
    prose = _prose(msg)
    case.prose = prose[:320]
    case.ms = ms
    paths = _paths(msg)
    branches = _branches(msg)
    tools = _tools(msg)
    errors: list[str] = []
    expect = case.expect

    if expect == "agent_help":
        if not prose:
            errors.append("prosa vazia")
        if not AGENTE_RE.search(prose) and "+" not in prose:
            errors.append("sem guidance agente/composer")
        if tools:
            errors.append("tool operacional indevida")
        if "sb1010" in prose.lower() or "select " in prose.lower():
            errors.append("roteamento SQL")
    elif expect == "guidance_stock":
        if tools:
            errors.append("tool ERP no comum")
        if not AGENTE_RE.search(prose) and "agente" not in prose.lower():
            errors.append("sem guidance agente")
    elif expect == "capabilities":
        if not prose or len(prose) < 20:
            errors.append("prosa curta")
        if any("/financial/rol" in p for p in paths):
            errors.append("executou ROL em capabilities")
        if ms > _LATENCY_NORMAL_MS * 2:
            errors.append(f"lento {ms}ms (capabilities sem shortcut?)")
    elif expect == "stock_path":
        if not any("/stock" in p or "stock" in p.lower() for p in paths):
            errors.append(f"sem path stock ({paths})")
        if not tools:
            errors.append("sem tools")
    elif expect == "structure_path":
        if not any("/structure" in p or "/analyser" in p for p in paths):
            errors.append(f"sem path structure ({paths})")
        if not tools:
            errors.append("sem tools")
    elif expect == "schedule_path":
        if not any("schedule" in p.lower() for p in paths):
            errors.append(f"sem schedule ({paths})")
    elif expect == "sql_authoring":
        low = prose.lower()
        if "```sql" not in low and "select " not in low:
            errors.append("sem bloco SQL")
        if any("schedule" in p.lower() for p in paths):
            errors.append("REST schedule no authoring")
        if any("/data/sql" in p for p in paths):
            errors.append("execute /data/sql no authoring")
        if LEAK_RE.search(prose):
            errors.append("leak prompt/especialista")
    elif expect == "identity_fast":
        if not prose:
            errors.append("prosa vazia")
        if DADOS_RE.search(prose):
            errors.append("notice dados consultados")
        if tools:
            errors.append("tool operacional")
        if ms > _LATENCY_IDENTITY_MS:
            errors.append(f"lento {ms}ms (heurística miss?)")
    elif expect == "guidance":
        if not AGENTE_RE.search(prose):
            errors.append("sem guidance agente")
        if any("/financial/rol" in p for p in paths):
            errors.append("executou ROL no comum")
    elif expect == "rol_01":
        if not any("/financial/rol" in p and "by-branch" not in p for p in paths):
            if any("by-branch" in p for p in paths):
                errors.append("by-branch")
            elif not paths:
                errors.append("sem tool ROL")
        br_norm = {str(b).zfill(2) for b in branches}
        if branches and "02" in br_norm and "01" in case.message:
            errors.append(f"filial extra {branches}")
        if ESTOQUE_RE.search(prose):
            errors.append("prosa estoque")
    elif expect == "compare_dual":
        execs = sum(1 for t in tools if "execute_external" in str(t.get("name") or ""))
        if execs < 2:
            errors.append(f"sem dual ({execs})")
        if not prose:
            errors.append("prosa vazia")
    elif expect == "branch_dual":
        execs = sum(1 for t in tools if "execute_external" in str(t.get("name") or ""))
        br_norm = {str(b).zfill(2) for b in branches}
        if execs < 2:
            errors.append(f"sem dual ({execs})")
        if branches and not ({"01", "02"} <= br_norm):
            errors.append(f"branches={branches}")
    elif expect == "data_answer":
        if not tools:
            errors.append("sem tools")
        elif not _data_answer_in_tools(msg):
            errors.append("sem dataAnswer em toolCalls.metadata")
        if not prose:
            errors.append("prosa vazia")
    elif expect == "text_task":
        if tools:
            errors.append("tools em text_task")
        if not prose or len(prose) < 15:
            errors.append("prosa curta")
    elif expect == "follow_up_operational":
        if not prose:
            errors.append("prosa vazia")
        if LEAK_RE.search(prose):
            errors.append("leak")
    elif expect == "leak_free":
        if LEAK_RE.search(prose):
            errors.append("leak na bolha")
    elif expect == "soft":
        if not prose or len(prose) < 8:
            errors.append("resposta vazia")
    elif expect == "system_tables_search":
        if not any("/system/tables/search" in p for p in paths):
            errors.append(f"sem /system/tables/search ({paths})")
        if not tools:
            errors.append("sem tools")
        route = _intent_route(msg)
        if str(route.get("subIntent") or "") != "system_metadata":
            errors.append(f"subIntent={route.get('subIntent')!r}")
        if not prose:
            errors.append("prosa vazia")
    elif expect == "system_schema":
        # Aceita /schema (roteiro canônico) ou /columns («quais colunas…»)
        if not any(("/schema" in p or "/columns" in p) for p in paths):
            errors.append(f"sem /schema|/columns ({paths})")
        if not any("/system/tables" in p for p in paths):
            errors.append(f"sem /system/tables ({paths})")
        if not tools:
            errors.append("sem tools")
        if "x3_tamanho" in prose.lower() or re.search(r"\bn registros\b", prose.lower()):
            errors.append("prosa genérica/técnica SX3")
        if not prose or len(prose) < 40:
            errors.append("prosa curta/inútil")
        route = _intent_route(msg)
        sub = str(route.get("subIntent") or "")
        if sub and sub not in {"system_metadata", "sql_generate", "sql_schema"}:
            errors.append(f"subIntent={sub!r}")
    elif expect == "system_indexes":
        if not any("/indexes" in p for p in paths):
            errors.append(f"sem /indexes ({paths})")
        if not tools:
            errors.append("sem tools")
        if not prose:
            errors.append("prosa vazia")
    elif expect == "system_clarify_column":
        # Não inventar SA1; prefer clarify/show_sql ou schema da tabela pedida
        if any("/data/sql" in p for p in paths):
            errors.append("execute SQL indevido")
        low = prose.lower()
        if "sa1" in low and "sb1" not in " ".join(paths).lower():
            # only fail if it jumped to SA1 via tool without user asking
            if any("/system/tables/SA1" in p or "/system/tables/sa1" in p.lower() for p in paths):
                errors.append("inventou SA1 via tool")
        if not prose:
            errors.append("prosa vazia")

    case.evidence = _build_evidence(case, msg, ms, errors)
    bits: list[str] = []
    if errors:
        case.status = "FAIL"
        bits.append("; ".join(errors))
    else:
        case.status = "PASS"
        bits.append("ok")
    bits.append(f"{ms}ms")
    if paths:
        bits.append(f"paths={paths[:4]}")
    if branches:
        bits.append(f"br={branches}")
    case.detail = " | ".join(bits)


def _cases_catalog() -> list[BatteryCase]:
    """Roteiros PT-BR com variação humana — espelham audit § 3."""
    cases: list[BatteryCase] = [
        # F01 — ativação
        BatteryCase("F01.1", "F01", "ativa-agente", "como ativo o agente?", "agent_help"),
        BatteryCase("F01.2", "F01", "qual-agente-produto", "qual agente consulta produto?", "agent_help"),
        BatteryCase(
            "F01.3",
            "F01",
            "estoque-sem-agente",
            "me fala o estq do 10080001 pf",
            "guidance_stock",
        ),
        # F02 — capabilities
        BatteryCase("F02.1", "F02", "o-que-faz", "o q vc pode fazer?", "capabilities"),
        BatteryCase("F02.2", "F02", "guia-estoque", "me guie na consulta de estoque", "guidance"),
        # F03 — REST operacional
        BatteryCase(
            "F03.1",
            "F03",
            "estoque-codigo",
            "estoque do 10080047",
            "stock_path",
            use_agent=True,
            r_required=("R1", "R2", "R3", "R4", "R5", "R8"),
        ),
        BatteryCase(
            "F03.2-typo-estrutra",
            "F03",
            "estrutra-produto",
            "qual a estrutra do 90260148?",
            "structure_path",
            use_agent=True,
            r_required=("R1", "R2", "R3", "R4", "R8"),
        ),
        BatteryCase(
            "F03.3-rol-abrev",
            "F03",
            "rol-ago-abrev",
            "rol 01 ago/26",
            "rol_01",
            use_agent=True,
        ),
        BatteryCase(
            "F03.4-typo-filail",
            "F03",
            "rol-filail",
            "rol da filail 01 em agosto/2026",
            "rol_01",
            use_agent=True,
        ),
        BatteryCase(
            "F03.5-schedule-casual",
            "F03",
            "programado-hoje",
            "qtos tem programado p produzir hj?",
            "schedule_path",
            use_agent=True,
        ),
        BatteryCase(
            "F03.6-follow-fornecedores",
            "F03",
            "follow-fornecedores",
            "e os fornecedores?",
            "follow_up_operational",
            use_agent=True,
            seed=["ficha do produto 10080047"],
            reuse_session=True,
            r_required=("R1", "R2", "R6", "R4", "R8"),
        ),
        # F04 — SQL authoring
        BatteryCase(
            "F04.1",
            "F04",
            "sql-grupo-1008",
            "crie um sql q liste os 10 primeiros produtos do grupo 1008",
            "sql_authoring",
            use_agent=True,
        ),
        BatteryCase(
            "F04.2",
            "F04",
            "select-sb1",
            "monta um select da SB1 sem executar",
            "sql_authoring",
            use_agent=True,
        ),
        BatteryCase(
            "F04.leak",
            "F04",
            "sql-sem-leak",
            "crie sql top 10 SB1 grupo 1008",
            "sql_authoring",
            use_agent=True,
        ),
        # F06 — metadado Protheus /system
        BatteryCase(
            "F06.search",
            "F06",
            "tabela-produtos",
            "qual a tabela de produtos?",
            "system_tables_search",
            use_agent=True,
            r_required=("R1", "R2", "R4", "R8"),
        ),
        BatteryCase(
            "F06.schema",
            "F06",
            "schema-sb1010",
            "me mostre o schema da tabela SB1010",
            "system_schema",
            use_agent=True,
            r_required=("R1", "R2", "R3", "R4", "R8"),
        ),
        BatteryCase(
            "F06.columns",
            "F06",
            "colunas-sb1010",
            "quais colunas da tabela SB1010?",
            "system_schema",
            use_agent=True,
            r_required=("R1", "R2", "R3", "R4", "R8"),
        ),
        BatteryCase(
            "F06.indexes",
            "F06",
            "indexes-sb1010",
            "quais indexes da SB1010?",
            "system_indexes",
            use_agent=True,
            r_required=("R1", "R2", "R3", "R4", "R8"),
        ),
        BatteryCase(
            "F06.addcol",
            "F06",
            "addcol-desconhecida",
            "adicione a coluna cidade nessa consulta",
            "system_clarify_column",
            use_agent=True,
            seed=["crie um sql que liste produtos do grupo 1008 sem executar"],
            reuse_session=True,
            r_required=("R1", "R2", "R4", "R6", "R8"),
        ),
        # F14 — follow-up
        BatteryCase(
            "F14.1-filial",
            "F14",
            "follow-filial-01",
            "somente filial 01",
            "follow_up_operational",
            use_agent=True,
            seed=["qual o estoque do produto 10080001?"],
            reuse_session=True,
            r_required=("R1", "R6", "R4", "R8"),
        ),
        BatteryCase(
            "F14.2-mes-passado",
            "F14",
            "follow-mes-passado",
            "e no mês passado?",
            "compare_dual",
            use_agent=True,
            seed=["ROL filial 01 agosto 2026"],
            reuse_session=True,
            r_required=("R1", "R6", "R2", "R4", "R8"),
        ),
        # F16 — text task
        BatteryCase(
            "F16.1",
            "F16",
            "email-formal",
            "deixe mais formal: preciso q envie o relatório hoje",
            "text_task",
        ),
        # F19 — identidade
        BatteryCase("F19-B2", "F19", "identity-vc", "como vc se chama?", "identity_fast", r_required=("R1", "R2", "R4", "R8")),
        BatteryCase("F19-B4", "F19", "identity-chamar", "como posso te chamar?", "identity_fast", r_required=("R1", "R2", "R4", "R8")),
        BatteryCase("F19-small", "F19", "bom-dia", "bom dia", "soft", r_required=("R1", "R2", "R4")),
        # F23 — leak (validado no sql_authoring)
        BatteryCase(
            "F23.1",
            "F23",
            "pos-sql-sem-leak",
            "monta select SB1 top 5",
            "leak_free",
            use_agent=True,
            r_required=("R4",),
        ),
        # Herança eval A–D (compare / dataAnswer)
        BatteryCase(
            "C1-consolidado",
            "F03",
            "rol-consolidado",
            "qual o rol consolidado em agosto 2026",
            "data_answer",
            use_agent=True,
        ),
        BatteryCase(
            "D5-typo-filiais",
            "F03",
            "compare-filial-typo",
            "compara filail 01 vs filail 02",
            "branch_dual",
            use_agent=True,
            seed=["ROL filial 01 agosto 2026"],
            reuse_session=True,
        ),
    ]
    return cases


def _send_turn(
    token: str,
    session_id: str,
    message: str,
    *,
    agent_id: str | None,
    response_mode: str,
) -> tuple[dict, int]:
    body: dict[str, Any] = {
        "message": message,
        "responseMode": response_mode,
        "includeAdminDebug": True,
    }
    if agent_id:
        body["agentId"] = agent_id
    t0 = time.perf_counter()
    payload = _request(
        "POST",
        f"{_BASE}{_CHAT}/sessions/{session_id}/messages",
        token=token,
        body=body,
    )
    ms = int((time.perf_counter() - t0) * 1000)
    return _unwrap_message(payload), ms


def _run_case(
    token: str,
    agent_id: str | None,
    case: BatteryCase,
    session_cache: dict[str, str],
) -> str:
    print(f"\n→ [{case.case_id}] {case.message!r}", flush=True)
    aid = agent_id if case.use_agent else None
    cache_key = f"{aid or 'common'}:{case.case_id}" if case.reuse_session else f"{aid or 'common'}:ephemeral"
    sid = session_cache.get(cache_key) if case.reuse_session else None
    if not sid:
        body: dict[str, Any] = {"title": f"battery-{case.case_id}"[:60]}
        if aid:
            body["agentId"] = aid
        session = _request("POST", f"{_BASE}{_CHAT}/sessions", token=token, body=body)
        sid = str(session["id"])
        if case.reuse_session:
            session_cache[cache_key] = sid
    try:
        for seed_msg in case.seed:
            print(f"  seed: {seed_msg!r}", flush=True)
            _send_turn(token, sid, seed_msg, agent_id=aid, response_mode=case.response_mode)
        msg, ms = _send_turn(
            token, sid, case.message, agent_id=aid, response_mode=case.response_mode
        )
        _judge(case, msg, ms)
    except Exception as exc:  # noqa: BLE001
        case.status = "FAIL"
        case.detail = str(exc)[:400]
    print(f"  [{case.status}] {case.detail}", flush=True)
    if case.prose:
        print(f"  prosa: {case.prose.replace(chr(10), ' ')[:200]}", flush=True)
    if not case.reuse_session:
        session_cache.pop(cache_key, None)
    return token


def _filter_cases(cases: list[BatteryCase]) -> list[BatteryCase]:
    only = {x.strip() for x in os.environ.get("SMOKE_ONLY", "").split(",") if x.strip()}
    families = {x.strip().upper() for x in os.environ.get("SMOKE_FAMILY", "").split(",") if x.strip()}
    skip_opt = os.environ.get("SMOKE_SKIP_OPTIONAL", "").strip() in {"1", "true", "yes"}
    out: list[BatteryCase] = []
    for case in cases:
        if only and case.case_id not in only and case.label not in only:
            continue
        if families and case.family.upper() not in families:
            continue
        if skip_opt and case.optional:
            continue
        out.append(case)
    return out


def _write_report(cases: list[BatteryCase], path: str) -> None:
    existing: list[dict] = []
    only = os.environ.get("SMOKE_ONLY", "").strip()
    if only and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                existing = json.load(fh)
        except Exception:
            existing = []
    fresh = [
        {
            "caseId": c.case_id,
            "family": c.family,
            "label": c.label,
            "message": c.message,
            "expect": c.expect,
            "useAgent": c.use_agent,
            "seed": c.seed,
            "responseMode": c.response_mode,
            "status": c.status,
            "detail": c.detail,
            "ms": c.ms,
            "prose": c.prose,
            "evidence": c.evidence,
            "rRequired": list(c.r_required),
        }
        for c in cases
    ]
    if existing:
        by_id = {row["caseId"]: row for row in existing if isinstance(row, dict) and row.get("caseId")}
        for row in fresh:
            by_id[row["caseId"]] = row
        payload = list(by_id.values())
    else:
        payload = fresh
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def _list_cases() -> int:
    cases = _filter_cases(_cases_catalog())
    for c in cases:
        agent = "agent" if c.use_agent else "comum"
        seed = f" seed={len(c.seed)}" if c.seed else ""
        print(f"{c.case_id}\t{c.family}\t{agent}\t{c.expect}\t{c.message[:60]}{seed}")
    print(f"\nTOTAL {len(cases)} casos")
    return 0


def main() -> int:
    if "--list-cases" in sys.argv or "--dry-run" in sys.argv:
        return _list_cases()

    print(f"base={_BASE}", flush=True)
    print("auth…", flush=True)
    token = _token()
    agent_id = _first_agent(token)
    print(f"agent={agent_id}", flush=True)

    cases = _filter_cases(_cases_catalog())
    if not cases:
        print("Nenhum caso após filtro.", file=sys.stderr)
        return 2

    session_cache: dict[str, str] = {}
    for case in cases:
        token = _run_case(token, agent_id, case, session_cache)

    passed = sum(1 for c in cases if c.status == "PASS")
    failed = sum(1 for c in cases if c.status == "FAIL")
    skipped = sum(1 for c in cases if c.status == "SKIP")

    print("\n=== BATERIA INTERAÇÃO HUMANA ===")
    by_family: dict[str, list[BatteryCase]] = {}
    for c in cases:
        by_family.setdefault(c.family, []).append(c)
    for family in sorted(by_family):
        items = by_family[family]
        ok = sum(1 for i in items if i.status == "PASS")
        print(f"  {family}: {ok}/{len(items)} PASS")
        for i in items:
            print(f"    [{i.status}] {i.case_id} — {i.detail}")

    print(f"\nTOTAL PASS={passed} FAIL={failed} SKIP={skipped}")

    out = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "docs",
            "testing",
            "evidence",
            "chat-human-interaction-battery.json",
        )
    )
    _write_report(cases, out)
    print(f"wrote {out}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
