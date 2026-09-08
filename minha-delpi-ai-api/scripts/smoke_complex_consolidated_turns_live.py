#!/usr/bin/env python3
"""Smoke live — turnos complexos com pedido multi-informação e apresentação rica.

Avalia se o chat consolida (prosa + KPI/tabela/gráfico/árvore/dashboard) o que
o usuário pediu numa única resposta (ou stack coerente no metadata).

Uso:
  docker exec -e SMOKE_BASE_URL=http://delpi-gateway -w /app delpi-minha-delpi-ai-api \\
    python scripts/smoke_complex_consolidated_turns_live.py

  # host
  SMOKE_BASE_URL=http://localhost PYTHONPATH=. .venv/bin/python -u \\
    scripts/smoke_complex_consolidated_turns_live.py
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
_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip() or "normal"
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "90260149").strip()
_PAUSE = float(os.environ.get("SMOKE_CASE_PAUSE", "4"))
_AGENT_ID = os.environ.get("SMOKE_AGENT_ID", "").strip()
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/testing/evidence/chat-complex-consolidated-turns-live.json",
).strip()

# Preferências de path por caso (subset mínimo que cobre o pedido).
_PRODUCT_PATH_PREFS = (
    "/analyser",
    "/structure",
    "/stock",
    "/open-orders",
    "/guide",
    "/sales",
    "/rol",
    "/commercial",
    "/kpi",
)


CASES: list[dict[str, Any]] = [
    {
        "id": "C1-analyser-integrado",
        "message": (
            f"Me dá uma visão integrada do produto {_PRODUCT}: ficha/cadastro, "
            f"estrutura (árvore se houver), roteiro e estoque. Quero prosa clara "
            f"mais os painéis necessários (tabela/KPI/árvore), sem omitir o que "
            f"eu pedi."
        ),
        "expect_any_kinds": ["table", "kpi", "tree", "dashboard", "stack"],
        "expect_prose": True,
        "expect_min_tools": 1,
        "expect_min_rich_surfaces": 1,
        "expect_path_markers": ["/analyser", "/structure", "/stock", "/products/"],
        "expect_path_groups": [["/analyser"], ["/structure", "/stock"]],
        "forbid_sql_fence": True,
    },
    {
        "id": "C2-estrutura-estoque-pedidos",
        "message": (
            f"Para o produto {_PRODUCT}, traga numa resposta só: (1) estrutura de "
            f"bom/componentes, (2) saldo de estoque atual e (3) pedidos de venda "
            f"em aberto se existirem. Consolide com tabelas e um resumo executivo; "
            f"se faltar algum bloco, diga explicitamente o que faltou."
        ),
        "expect_any_kinds": ["table", "kpi", "tree", "dashboard"],
        "expect_prose": True,
        "expect_min_tools": 2,
        "expect_min_rich_surfaces": 1,
        "expect_path_markers": ["/structure", "/stock", "/open-orders", "/sales", "/products/"],
        "expect_path_groups": [["/structure"], ["/stock"], ["/open-orders", "/sales"]],
        "forbid_sql_fence": True,
    },
    {
        "id": "C3-kpi-serie-comercial",
        "message": (
            "Quero o ROL / indicadores comerciais recentes: mostre o número "
            "principal (KPI), a série no tempo em gráfico se disponível, e uma "
            "leitura em prosa do que está acontecendo — tudo na mesma resposta."
        ),
        "expect_any_kinds": ["kpi", "chart", "table", "dashboard"],
        "expect_prose": True,
        "expect_min_tools": 1,
        "expect_min_rich_surfaces": 1,
        "expect_path_markers": ["/rol", "/commercial", "/kpi", "/sales", "/billing"],
        "forbid_sql_fence": True,
        "forbid_path_markers": ["/stock"],
    },
    {
        "id": "C4-multi-ask-followup",
        "seed": f"estoque e descrição do produto {_PRODUCT}",
        "message": (
            "Agora completa: inclui também a estrutura e um comentário se o "
            "estoque cobre demanda típica. Quero visão consolidada (prosa + "
            "tabela/árvore), não só um bloco."
        ),
        "expect_any_kinds": ["table", "tree", "kpi", "dashboard", "stack"],
        "expect_prose": True,
        "expect_min_tools": 1,
        "expect_min_rich_surfaces": 1,
        "expect_path_markers": ["/structure", "/stock", "/products/"],
        "expect_path_groups": [["/structure"], ["/stock", "/products/"]],
        "forbid_sql_fence": True,
    },
]


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 420,
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


def _first_agent(token: str) -> str:
    if _AGENT_ID:
        return _AGENT_ID

    payload = _request("GET", f"{_BASE}{_CHAT}/agents?limit=50", token=token)
    items = payload if isinstance(payload, list) else payload.get("items") or []
    if not items:
        raise RuntimeError("nenhum agente disponível")

    scored: list[tuple[int, str, str]] = []
    for agent in items:
        if agent.get("enabled") is False:
            continue
        agent_id = str(agent.get("id") or "").strip()
        if not agent_id:
            continue
        meta = agent.get("metadata") if isinstance(agent.get("metadata"), dict) else {}
        caps = meta.get("capabilities") if isinstance(meta.get("capabilities"), dict) else {}
        allowed = meta.get("allowed_actions")
        if not isinstance(allowed, list):
            allowed = meta.get("allowedActions") if isinstance(meta.get("allowedActions"), list) else []
        score = 0
        if caps.get("actions") is True or caps.get("actions") is None:
            score += 10
        max_tools = int(agent.get("max_tool_calls") or agent.get("maxToolCalls") or 0)
        score += min(max_tools, 12)
        # Lista vazia = catálogo amplo (preferir); lista explícita pontua por paths produto.
        if not allowed:
            score += 20
        else:
            blob = " ".join(
                str(
                    item.get("path")
                    if isinstance(item, dict)
                    else item
                )
                for item in allowed
            ).lower()
            score += sum(3 for marker in _PRODUCT_PATH_PREFS if marker in blob)
        name = str(agent.get("name") or "")
        scored.append((score, agent_id, name))

    if not scored:
        return str(items[0]["id"])

    scored.sort(key=lambda row: (-row[0], row[2].lower()))
    best = scored[0]
    print(f"agent_score={best[0]} name={best[2]!r}", flush=True)
    return best[1]


def _create_session(token: str, agent_id: str, title: str) -> str:
    session = _request(
        "POST",
        f"{_BASE}{_CHAT}/sessions",
        token=token,
        body={"title": title[:80], "agentId": agent_id},
    )
    return str(session["id"])


def _send(
    token: str,
    session_id: str,
    agent_id: str,
    message: str,
) -> tuple[dict, int]:
    body = {
        "message": message,
        "agentId": agent_id,
        "responseMode": _MODE,
        "includeAdminDebug": True,
        "adminDebug": True,
    }
    t0 = time.perf_counter()
    payload = _request(
        "POST",
        f"{_BASE}{_CHAT}/sessions/{session_id}/messages",
        token=token,
        body=body,
    )
    wall_ms = int((time.perf_counter() - t0) * 1000)
    return payload, wall_ms


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


def _extract_latency(msg: dict, wall_ms: int) -> dict[str, Any]:
    admin = _admin(msg)
    intel = admin.get("intelligence") if isinstance(admin.get("intelligence"), dict) else {}
    timings = intel.get("timings") if isinstance(intel.get("timings"), dict) else {}
    if not timings and isinstance(admin.get("timings"), dict):
        timings = admin["timings"]
    metrics = admin.get("metrics") if isinstance(admin.get("metrics"), dict) else {}
    llm = admin.get("llm") if isinstance(admin.get("llm"), dict) else {}
    llm_usage = llm.get("usage") if isinstance(llm.get("usage"), dict) else {}
    tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
    pipeline = intel.get("pipeline") if isinstance(intel.get("pipeline"), dict) else {}

    stages = {
        "preToolMs": timings.get("preToolMs"),
        "toolsMs": timings.get("toolsMs"),
        "postToolMs": timings.get("postToolMs"),
        "ragMs": timings.get("ragMs"),
        "llmMs": timings.get("llmMs"),
        "totalMs": timings.get("totalMs") or metrics.get("latencyMs") or llm_usage.get("latencyMs"),
    }
    breakdown = timings.get("toolsBreakdown") if isinstance(timings.get("toolsBreakdown"), dict) else {}
    selection = (
        breakdown.get("selectionBreakdown")
        if isinstance(breakdown.get("selectionBreakdown"), dict)
        else {}
    )

    # Gargalo = maior estágio conhecido (exceto total)
    stage_pairs = [
        (name, int(value))
        for name, value in stages.items()
        if name != "totalMs" and isinstance(value, (int, float)) and value is not None
    ]
    bottleneck = max(stage_pairs, key=lambda item: item[1]) if stage_pairs else ("unknown", 0)

    return {
        "wallMs": wall_ms,
        "stages": stages,
        "toolsBreakdown": {
            key: breakdown.get(key)
            for key in (
                "selectionMs",
                "wave1Ms",
                "wave1HttpMs",
                "wave1PresentationMs",
                "criticMs",
                "wave2Ms",
                "wave2HttpMs",
                "wave2PresentationMs",
                "assembleMs",
                "agenticExtendMs",
                "finalizeAfterToolsMs",
            )
            if breakdown.get(key) is not None
        },
        "selectionBreakdown": {
            key: selection.get(key)
            for key in (
                "selectionNativeMs",
                "selectionRouterMs",
                "selectionPlanMs",
                "selectionDispatchMs",
                "selectionEmbedMs",
                "selectionCandidateDbMs",
            )
            if selection.get(key) is not None
        },
        "preToolBreakdown": (
            timings.get("preToolBreakdown")
            if isinstance(timings.get("preToolBreakdown"), dict)
            else {}
        ),
        "bottleneckStage": bottleneck[0],
        "bottleneckMs": bottleneck[1],
        "skipRag": bool(pipeline.get("skipRag")) if pipeline else None,
        "fastPath": bool(pipeline.get("fastPath")) if pipeline else None,
        "toolCountAdmin": tooling.get("toolCount") or intel.get("toolCount"),
    }


def _assistant_text(response: dict) -> str:
    msg = _unwrap(response)
    for key in ("answer", "content", "message", "text"):
        value = msg.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("assistantMessage", "assistant"):
        block = response.get(key)
        if isinstance(block, dict):
            for nested in ("content", "text", "answer"):
                value = block.get(nested)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        if isinstance(block, str) and block.strip():
            return block.strip()
    return ""


def _tool_metas(response: dict) -> list[dict]:
    msg = _unwrap(response)
    out: list[dict] = []
    for call in msg.get("toolCalls") or response.get("toolCalls") or []:
        if not isinstance(call, dict):
            continue
        meta = call.get("metadata")
        if isinstance(meta, dict):
            out.append(meta)
    if out:
        return out
    admin = _admin(msg)
    tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
    for call in tooling.get("toolCalls") or []:
        if isinstance(call, dict) and isinstance(call.get("metadata"), dict):
            out.append(call["metadata"])
    return out


def _collect_presentation_kinds(metas: list[dict], response: dict) -> set[str]:
    kinds: set[str] = set()

    def _scan(meta: dict) -> None:
        for key, kind in (
            ("kpiPresentation", "kpi"),
            ("chartPresentation", "chart"),
            ("treePresentation", "tree"),
            ("dashboardPresentation", "dashboard"),
            ("tablePresentation", "table"),
            ("presentation", None),
            ("profileTablePresentation", "table"),
        ):
            block = meta.get(key)
            if not isinstance(block, dict):
                continue
            if kind:
                kinds.add(kind)
            else:
                ptype = str(block.get("type") or "").strip().lower()
                if ptype:
                    kinds.add(ptype if ptype != "line_chart" else "chart")
        tables = meta.get("tablePresentations")
        if isinstance(tables, list) and tables:
            kinds.add("table")
        decision = meta.get("presentationDecision")
        if isinstance(decision, dict):
            selected = str(decision.get("selected") or "").strip().lower()
            layout = str(decision.get("layoutMode") or "").strip().lower()
            if selected:
                kinds.add("chart" if selected in {"line_chart", "bar_chart"} else selected)
            if layout == "stack":
                kinds.add("stack")
        plan = meta.get("stackPresentationPlan") or meta.get("renderPlan")
        if isinstance(plan, dict) and plan:
            kinds.add("stack")
        if meta.get("dataAnswer") or meta.get("dataCommentary"):
            kinds.add("prose_structured")
        if meta.get("resolvedFieldLabels"):
            kinds.add("field_labels")

    for meta in metas:
        _scan(meta)
    # top-level fallback
    if isinstance(response.get("metadata"), dict):
        _scan(response["metadata"])
    return kinds


def _paths(metas: list[dict]) -> list[str]:
    paths: list[str] = []
    for meta in metas:
        path = str(meta.get("path") or "").strip()
        if path:
            paths.append(path)
    return paths


def _pipeline_stages(msg: dict) -> list[str]:
    admin = _admin(msg)
    intel = admin.get("intelligence") if isinstance(admin.get("intelligence"), dict) else {}
    pipeline = intel.get("pipeline") if isinstance(intel.get("pipeline"), dict) else {}
    stages = pipeline.get("stages") or admin.get("pipelineStages") or intel.get("stages")
    if isinstance(stages, list):
        return [str(item) for item in stages if str(item).strip()]
    return []


def _eval_case(case: dict[str, Any], response: dict, wall_ms: int) -> dict[str, Any]:
    msg = _unwrap(response)
    prose = _assistant_text(response)
    metas = _tool_metas(response)
    kinds = _collect_presentation_kinds(metas, msg)
    paths = _paths(metas)
    ok_tools = [m for m in metas if m.get("ok") is True]
    latency = _extract_latency(msg, wall_ms)
    stages = _pipeline_stages(msg)
    errors: list[str] = []

    if case.get("expect_prose") and len(prose) < 40:
        errors.append(f"prosa curta/ausente ({len(prose)} chars)")

    if case.get("forbid_sql_fence") and "```sql" in prose.lower():
        errors.append("prosa operacional contém fence ```sql")

    if len(ok_tools) < int(case.get("expect_min_tools") or 0):
        errors.append(f"tools ok={len(ok_tools)} < {case.get('expect_min_tools')}")

    expected_kinds = set(case.get("expect_any_kinds") or [])
    if expected_kinds and not (kinds & expected_kinds):
        errors.append(f"nenhum kind esperado {sorted(expected_kinds)}; got={sorted(kinds)}")

    markers = case.get("expect_path_markers") or []
    if markers:
        joined = " ".join(paths).lower()
        if not any(str(marker).lower() in joined for marker in markers):
            if not paths:
                errors.append("nenhum path de tool")
            else:
                errors.append(f"paths {paths} sem markers {markers}")

    path_groups = case.get("expect_path_groups") or []
    if path_groups:
        joined = " ".join(paths).lower()
        matched_groups = 0
        for group in path_groups:
            if any(str(marker).lower() in joined for marker in group):
                matched_groups += 1
        # Para pedidos compostos, exigir pelo menos 2 grupos cobertos quando há ≥2 grupos.
        min_groups = min(2, len(path_groups)) if len(path_groups) >= 2 else 1
        if matched_groups < min_groups:
            errors.append(
                f"path groups cobertos={matched_groups} < {min_groups}; "
                f"paths={paths} groups={path_groups}"
            )

    forbid_paths = case.get("forbid_path_markers") or []
    if forbid_paths and paths:
        joined = " ".join(paths).lower()
        # Só falha se o único path for o proibido (ex.: C3 só /stock).
        if all(
            any(str(marker).lower() in path.lower() for marker in forbid_paths)
            for path in paths
        ) and not any(
            marker in joined
            for marker in ("/rol", "/commercial", "/kpi", "/billing", "/sales")
            if marker not in {str(item).lower() for item in forbid_paths}
        ):
            errors.append(f"paths só com marcadores proibidos {forbid_paths}: {paths}")

    rich_surfaces = kinds & {"table", "kpi", "chart", "tree", "dashboard", "stack"}
    min_rich = int(case.get("expect_min_rich_surfaces") or 1)
    if len(rich_surfaces) < min_rich:
        errors.append(
            f"rich surfaces={sorted(rich_surfaces)} < {min_rich}"
        )

    return {
        "id": case["id"],
        "passed": not errors,
        "errors": errors,
        "proseChars": len(prose),
        "prosePreview": prose[:280],
        "kinds": sorted(kinds),
        "richSurfaces": sorted(rich_surfaces),
        "toolCount": len(metas),
        "okToolCount": len(ok_tools),
        "paths": paths,
        "pipelineStages": stages,
        "hasResolvedFieldLabels": "field_labels" in kinds,
        "latency": latency,
    }


def _print_latency(latency: dict[str, Any]) -> None:
    stages = latency.get("stages") or {}
    print(
        "  latency wall={wall}ms total={total} preTool={pre} tools={tools} "
        "postTool={post} rag={rag} llm={llm} bottleneck={bn}({bnms}ms)".format(
            wall=latency.get("wallMs"),
            total=stages.get("totalMs"),
            pre=stages.get("preToolMs"),
            tools=stages.get("toolsMs"),
            post=stages.get("postToolMs"),
            rag=stages.get("ragMs"),
            llm=stages.get("llmMs"),
            bn=latency.get("bottleneckStage"),
            bnms=latency.get("bottleneckMs"),
        ),
        flush=True,
    )
    tools_bd = latency.get("toolsBreakdown") or {}
    if tools_bd:
        parts = [f"{k}={v}" for k, v in tools_bd.items()]
        print(f"  toolsBreakdown {' '.join(parts)}", flush=True)
    sel = latency.get("selectionBreakdown") or {}
    if sel:
        parts = [f"{k}={v}" for k, v in sel.items()]
        print(f"  selectionBreakdown {' '.join(parts)}", flush=True)


def main() -> int:
    print(f"base={_BASE} mode={_MODE} product={_PRODUCT}", flush=True)
    token = _token()
    agent_id = _first_agent(token)
    print(f"agent={agent_id}", flush=True)

    results: list[dict[str, Any]] = []
    failed = 0

    for index, case in enumerate(CASES):
        if index:
            time.sleep(_PAUSE)
        print("=" * 72, flush=True)
        print(f"CASE {case['id']}", flush=True)
        print(f"MSG  {case['message'][:120]}…", flush=True)
        try:
            sid = _create_session(token, agent_id, f"live-complex-{case['id']}")
            if case.get("seed"):
                _send(token, sid, agent_id, str(case["seed"]))
                time.sleep(max(1.0, _PAUSE / 2))
            response, wall_ms = _send(token, sid, agent_id, str(case["message"]))
            evaluated = _eval_case(case, response, wall_ms)
            evaluated["sessionId"] = sid
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:500]
            evaluated = {
                "id": case["id"],
                "passed": False,
                "errors": [f"HTTP {exc.code}: {body}"],
                "latency": {"wallMs": None, "bottleneckStage": "http_error"},
            }
        except Exception as exc:  # noqa: BLE001 — smoke live
            evaluated = {
                "id": case["id"],
                "passed": False,
                "errors": [f"{type(exc).__name__}: {exc}"],
                "latency": {"wallMs": None, "bottleneckStage": "exception"},
            }

        results.append(evaluated)
        status = "PASS" if evaluated["passed"] else "FAIL"
        print(f"{status} kinds={evaluated.get('kinds')} paths={evaluated.get('paths')}", flush=True)
        if evaluated.get("latency"):
            _print_latency(evaluated["latency"])
        if evaluated.get("errors"):
            for err in evaluated["errors"]:
                print(f"  - {err}", flush=True)
            failed += 1
        else:
            print(
                f"  prose={evaluated.get('proseChars')}c rich={evaluated.get('richSurfaces')}",
                flush=True,
            )
            preview = evaluated.get("prosePreview") or ""
            if preview:
                print(f"  preview: {preview[:160]}…", flush=True)

    # Resumo de latência / gargalos
    walls = [
        int(r["latency"]["wallMs"])
        for r in results
        if isinstance(r.get("latency"), dict) and isinstance(r["latency"].get("wallMs"), int)
    ]
    bottlenecks: dict[str, int] = {}
    for result in results:
        latency = result.get("latency") if isinstance(result.get("latency"), dict) else {}
        stage = str(latency.get("bottleneckStage") or "unknown")
        bottlenecks[stage] = bottlenecks.get(stage, 0) + 1

    evidence = {
        "baseUrl": _BASE,
        "responseMode": _MODE,
        "productCode": _PRODUCT,
        "agentId": agent_id,
        "passed": failed == 0,
        "failCount": failed,
        "caseCount": len(results),
        "latencySummary": {
            "wallsMs": walls,
            "avgWallMs": int(sum(walls) / len(walls)) if walls else None,
            "maxWallMs": max(walls) if walls else None,
            "minWallMs": min(walls) if walls else None,
            "bottleneckCounts": bottlenecks,
        },
        "results": results,
    }
    out_path = _OUT
    if not os.path.isabs(out_path):
        out_path = os.path.join(os.getcwd(), out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, ensure_ascii=False, indent=2)
    print("=" * 72, flush=True)
    print(f"evidence={out_path}", flush=True)
    print(
        "LATENCY avg={avg}ms min={mn}ms max={mx}ms bottlenecks={bn}".format(
            avg=evidence["latencySummary"]["avgWallMs"],
            mn=evidence["latencySummary"]["minWallMs"],
            mx=evidence["latencySummary"]["maxWallMs"],
            bn=bottlenecks,
        ),
        flush=True,
    )
    print(
        f"SUMMARY {'PASS' if failed == 0 else 'FAIL'} ({len(results) - failed}/{len(results)})",
        flush=True,
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
