#!/usr/bin/env python3
"""Live conversation smoke — Presentation Composer multi-turn (uma sessão).

Turnos na mesma conversa:
  T1 estoque → tabela
  T2 gráfico de barras
  T3 mapa de calor (materializa se ≥2 dims discriminantes; senão unmet + notice)
  T4 lousa deíctica → canvasOpen real (clarificação = FAIL)

Produtos padrão (podem sobrescrever via SMOKE_PC_PRODUCTS):
  - PA 90260149
  - matéria-prima 10080001

Uso:
  cd minha-delpi-ai-api
  SMOKE_BASE_URL=http://localhost \\
    PYTHONPATH=. .venv/bin/python -u scripts/smoke_presentation_composer_conversation_live.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip() or "http://localhost"
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USER = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip() or "normal"
_PRODUCTS = [
    item.strip()
    for item in os.environ.get("SMOKE_PC_PRODUCTS", "90260149,10080001").split(",")
    if item.strip()
]
_TIMEOUT = float(os.environ.get("SMOKE_HTTP_TIMEOUT", "420"))
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/testing/evidence/presentation-composer-conversation-live.json",
).strip()


def _turns_for(product: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "T1.stock_table",
            "message": (
                f"Consulte o estoque do produto {product} via ferramenta de estoque/saldo "
                "(não inspeção). Mostre em tabela."
            ),
            "expect": "table_or_rows",
        },
        {
            "id": "T2.chart_followup",
            "message": "Com esses mesmos dados de estoque, mostre em um gráfico de barras.",
            "expect": "chart",
        },
        {
            "id": "T3.heatmap_or_notice",
            "message": (
                "Agora coloque isso em um gráfico de mapa de calor "
                "(produto × depósito/filial) em tons de azul."
            ),
            "expect": "heatmap_materialized_if_dims",
        },
        {
            "id": "T4.canvas",
            "message": "Coloque esse resultado na lousa.",
            "expect": "canvas_open",
        },
    ]


_DIM_FIELD_HINTS = (
    "branch",
    "filial",
    "warehouse",
    "armazem",
    "armazém",
    "deposito",
    "depósito",
    "deposit",
    "turno",
    "shift",
    "maquina",
    "máquina",
    "machine",
    "local",
    "location",
)


def _ok(label: str, detail: str = "") -> None:
    print(f"PASS  {label}" + (f" — {detail}" if detail else ""), flush=True)


def _fail(label: str, detail: str) -> None:
    print(f"FAIL  {label} — {detail}", flush=True)


def _warn(label: str, detail: str) -> None:
    print(f"WARN  {label} — {detail}", flush=True)


def _http(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 120,
) -> Any:
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
        return json.loads(raw) if raw else None


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
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"token missing: {payload}")
    return str(token)


def _agent(token: str) -> str:
    override = os.environ.get("SMOKE_AGENT_ID", "").strip()
    if override:
        return override
    agents = _http("GET", f"{_BASE}{_CHAT}/agents?limit=20", token=token)
    rows = agents if isinstance(agents, list) else (agents or {}).get("items") or []
    for row in rows:
        if isinstance(row, dict) and row.get("enabled"):
            return str(row.get("id") or row.get("agentId"))
    if not rows:
        raise RuntimeError("no agents")
    return str(rows[0].get("id") or rows[0].get("agentId"))


def _session(token: str, agent_id: str, *, title: str) -> str:
    payload = _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions",
        token=token,
        body={"agentId": agent_id, "title": title},
    )
    sid = (payload or {}).get("id") or (payload or {}).get("sessionId")
    if not sid:
        raise RuntimeError(f"session failed: {payload}")
    return str(sid)


def _send(token: str, session_id: str, message: str) -> dict:
    return _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": message,
            "responseMode": _MODE,
            "includeAdminDebug": True,
        },
        timeout=_TIMEOUT,
    ) or {}


def _walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _field_key(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("key") or value.get("field") or value.get("id") or value.get("label") or "")
    return str(value or "")


def _collect_dim_hints(node: dict[str, Any], out: set[str]) -> None:
    columns = node.get("columns")
    if isinstance(columns, list):
        for col in columns:
            key = _field_key(col).lower()
            if any(hint in key for hint in _DIM_FIELD_HINTS):
                out.add(key)
    for key_name in ("xField", "yField", "categoryKey", "seriesKey", "rowKey", "columnKey"):
        raw = node.get(key_name)
        if isinstance(raw, str) and any(hint in raw.lower() for hint in _DIM_FIELD_HINTS):
            out.add(raw.lower())
    cfg = node.get("config") if isinstance(node.get("config"), dict) else {}
    for key_name in ("xField", "yField", "xKey", "yKey", "rowKey", "columnKey", "categoryKey"):
        raw = cfg.get(key_name)
        if isinstance(raw, str) and any(hint in raw.lower() for hint in _DIM_FIELD_HINTS):
            out.add(raw.lower())


def _collect_discriminant_dims(node: dict[str, Any], out: set[str]) -> None:
    """Dims with ≥2 distinct values in sampled rows (true heatmap axes)."""
    rows = node.get("rows") or node.get("data")
    if not isinstance(rows, list) or len(rows) < 2:
        return
    columns = node.get("columns")
    keys: list[str] = []
    if isinstance(columns, list):
        keys = [_field_key(col) for col in columns if _field_key(col)]
    elif rows and isinstance(rows[0], dict):
        keys = [str(k) for k in rows[0].keys()]
    for key in keys:
        lowered = key.lower()
        if not any(hint in lowered for hint in _DIM_FIELD_HINTS):
            continue
        values = {
            str(row.get(key))
            for row in rows
            if isinstance(row, dict) and row.get(key) is not None
        }
        if len(values) >= 2:
            out.add(lowered)


def _presentation_snapshot(response: dict) -> dict[str, Any]:
    answer = str(response.get("answer") or response.get("content") or "")
    snap: dict[str, Any] = {
        "hasTable": False,
        "hasChart": False,
        "chartType": None,
        "paletteFamily": None,
        "bindingProvenance": None,
        "canvasOpen": False,
        "canvasOpenPayload": None,
        "deliveryPreferCanvas": False,
        "specApplied": None,
        "selected": None,
        "unmetIntent": None,
        "unmetIntentNotice": None,
        "dimHints": [],
        "discriminantDims": [],
        "paths": [],
        "answerExcerpt": answer[:480],
        "answerHasUnmetNotice": False,
        "answerLooksLikeClarification": False,
        "answerHasContextMissing": False,
    }
    dim_hints: set[str] = set()
    discriminant_dims: set[str] = set()
    for node in _walk(response):
        if not isinstance(node, dict):
            continue
        _collect_dim_hints(node, dim_hints)
        _collect_discriminant_dims(node, discriminant_dims)
        if node.get("type") == "table" and (node.get("rows") or node.get("columns")):
            snap["hasTable"] = True
        if node.get("type") == "chart":
            snap["hasChart"] = True
            snap["chartType"] = node.get("chartType") or snap["chartType"]
            cfg = node.get("config") if isinstance(node.get("config"), dict) else {}
            snap["paletteFamily"] = cfg.get("paletteFamily") or snap["paletteFamily"]
            snap["bindingProvenance"] = (
                cfg.get("bindingProvenance") or snap["bindingProvenance"]
            )
        if "chartPresentation" in node and isinstance(node["chartPresentation"], dict):
            chart = node["chartPresentation"]
            snap["hasChart"] = True
            snap["chartType"] = chart.get("chartType") or snap["chartType"]
            cfg = chart.get("config") if isinstance(chart.get("config"), dict) else {}
            snap["paletteFamily"] = cfg.get("paletteFamily") or snap["paletteFamily"]
            snap["bindingProvenance"] = (
                cfg.get("bindingProvenance") or snap["bindingProvenance"]
            )
            _collect_dim_hints(chart, dim_hints)
            _collect_dim_hints(cfg, dim_hints)
        if "tablePresentation" in node and isinstance(node["tablePresentation"], dict):
            snap["hasTable"] = True
            _collect_dim_hints(node["tablePresentation"], dim_hints)
        canvas = node.get("canvasOpen")
        if isinstance(canvas, dict) and (canvas.get("markdown") or canvas.get("title")):
            snap["canvasOpen"] = True
            snap["canvasOpenPayload"] = {
                "title": canvas.get("title"),
                "hasMarkdown": bool(canvas.get("markdown")),
                "sourceMessageId": canvas.get("sourceMessageId"),
            }
        elif canvas and not snap["canvasOpen"]:
            snap["canvasOpen"] = True
        if node.get("deliveryPreferCanvas"):
            snap["deliveryPreferCanvas"] = True
        pi = node.get("presentationIntelligence")
        if isinstance(pi, dict):
            if "specApplied" in pi:
                snap["specApplied"] = pi.get("specApplied")
            if pi.get("unmetIntent"):
                snap["unmetIntent"] = pi.get("unmetIntent")
        decision = node.get("presentationDecision")
        if isinstance(decision, dict):
            if decision.get("selected"):
                snap["selected"] = decision.get("selected")
            if decision.get("unmetIntent"):
                snap["unmetIntent"] = decision.get("unmetIntent")
            if decision.get("unmetIntentNotice"):
                snap["unmetIntentNotice"] = decision.get("unmetIntentNotice")
            elif decision.get("policyNotice") and decision.get("unmetIntent"):
                snap["unmetIntentNotice"] = decision.get("policyNotice")
        path = node.get("path")
        if isinstance(path, str) and path.startswith("/") and path not in snap["paths"]:
            snap["paths"].append(path)

    snap["dimHints"] = sorted(dim_hints)
    snap["discriminantDims"] = sorted(discriminant_dims)
    lowered = answer.lower()
    notice = str(snap.get("unmetIntentNotice") or "").lower()
    snap["answerHasUnmetNotice"] = bool(
        ("mapa de calor" in lowered and "não consegui" in lowered)
        or ("mapa de calor" in lowered and "nao consegui" in lowered)
        or ("dados disponíveis" in lowered and "mapa" in lowered)
        or ("dados disponiveis" in lowered and "mapa" in lowered)
        or (notice and notice[:40] in lowered)
        or ("insufficient" in lowered and "heatmap" in lowered)
    )
    snap["answerHasContextMissing"] = (
        "referência não identificada" in lowered
        or "referencia nao identificada" in lowered
        or "context_missing" in lowered
    )
    snap["answerLooksLikeClarification"] = bool(
        snap["answerHasContextMissing"]
        or "qual resultado" in lowered
        or "qual tabela" in lowered
        or "qual gráfico" in lowered
        or "qual grafico" in lowered
        or "última resposta ou a tabela" in lowered
        or "ultima resposta ou a tabela" in lowered
        or "pode esclarecer" in lowered
        or "preciso que você indique" in lowered
        or "preciso que voce indique" in lowered
        or ("ambígu" in lowered and "lousa" in lowered)
        or ("ambigu" in lowered and "lousa" in lowered)
        or ("responda com uma frase curta" in lowered and "lousa" in answer.lower())
    )
    return snap


def _grade(
    expect: str,
    snap: dict[str, Any],
    *,
    product: str,
    session_dim_hints: set[str] | None = None,
    session_discriminant_dims: set[str] | None = None,
) -> tuple[str, list[str]]:
    errors: list[str] = []
    dims = set(session_dim_hints or ()) | set(snap.get("dimHints") or ())
    discriminant = set(session_discriminant_dims or ()) | set(snap.get("discriminantDims") or [])
    if expect == "table_or_rows":
        if not snap["hasTable"] and not snap["hasChart"]:
            excerpt = snap["answerExcerpt"].lower()
            if product not in snap["answerExcerpt"] and "estoque" not in excerpt:
                errors.append("no_table_chart_or_stock_answer")
    elif expect == "chart":
        if not snap["hasChart"] and snap.get("selected") not in {
            "chart",
            "bar_chart",
            "line_chart",
            "heatmap",
            "horizontal_bar",
        }:
            errors.append("no_chart")
    elif expect == "heatmap_materialized_if_dims":
        chart_type = str(snap.get("chartType") or "").lower()
        selected = str(snap.get("selected") or "").lower()
        palette = str(snap.get("paletteFamily") or "").lower()
        unmet = str(snap.get("unmetIntent") or "")
        notice = str(snap.get("unmetIntentNotice") or "").strip()
        materialized = chart_type == "heatmap" or selected == "heatmap"
        honest_gap = bool(unmet and (notice or snap.get("answerHasUnmetNotice")))
        # Require real heatmap only when ≥2 dims have cardinality ≥2 in sampled rows.
        enough_dims = len(discriminant) >= 2
        if enough_dims and not materialized:
            errors.append(
                "expected_heatmap_materialized_with_dims "
                f"discriminant={sorted(discriminant)} dims={sorted(dims)} "
                f"chartType={chart_type} selected={selected} unmetIntent={unmet or None}"
            )
        elif not enough_dims and not materialized and not honest_gap:
            errors.append(
                "expected_heatmap_or_unmet_notice "
                f"discriminant={sorted(discriminant)} dims={sorted(dims)} "
                f"chartType={chart_type} selected={selected} "
                f"unmetIntent={unmet or None} notice={bool(notice)} "
                f"answerNotice={snap.get('answerHasUnmetNotice')}"
            )
        if materialized and palette and palette != "sequential-blue":
            errors.append(f"heatmap_palette_not_blue={palette}")
    elif expect == "canvas_open":
        payload = snap.get("canvasOpenPayload") if isinstance(snap.get("canvasOpenPayload"), dict) else {}
        if snap.get("answerLooksLikeClarification") or snap.get("answerHasContextMissing"):
            errors.append("canvas_clarification_or_context_missing")
        if not snap.get("canvasOpen"):
            errors.append("canvasOpen_missing")
        elif payload and not (payload.get("hasMarkdown") or payload.get("title")):
            errors.append("canvasOpen_payload_incomplete")
    return ("FAIL" if errors else "PASS"), errors


def _run_product(token: str, agent_id: str, product: str) -> tuple[list[dict[str, Any]], list[str]]:
    session_id = _session(
        token,
        agent_id,
        title=f"smoke-pc-conversation-live-{product}",
    )
    print(f"\n=== product={product} session={session_id} ===", flush=True)
    cases: list[dict[str, Any]] = []
    hard: list[str] = []
    session_dim_hints: set[str] = set()
    session_discriminant_dims: set[str] = set()

    for turn in _turns_for(product):
        started = time.perf_counter()
        case_id = f"{product}.{turn['id']}"
        try:
            response = _send(token, session_id, turn["message"])
            snap = _presentation_snapshot(response)
            session_dim_hints.update(snap.get("dimHints") or [])
            session_discriminant_dims.update(snap.get("discriminantDims") or [])
            status, errors = _grade(
                turn["expect"],
                snap,
                product=product,
                session_dim_hints=session_dim_hints,
                session_discriminant_dims=session_discriminant_dims,
            )
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            payload = snap.get("canvasOpenPayload") or {}
            detail = (
                f"table={snap['hasTable']} chart={snap['hasChart']} "
                f"type={snap['chartType']} palette={snap['paletteFamily']} "
                f"selected={snap['selected']} unmet={snap['unmetIntent']} "
                f"notice={bool(snap['unmetIntentNotice'])} "
                f"answerNotice={snap['answerHasUnmetNotice']} "
                f"dims={sorted(session_dim_hints)} "
                f"discriminant={sorted(session_discriminant_dims)} "
                f"canvas={snap['canvasOpen']} "
                f"canvasTitle={payload.get('title') if isinstance(payload, dict) else None} "
                f"ms={elapsed}"
            )
            if status == "PASS":
                _ok(case_id, detail)
            else:
                _fail(case_id, "; ".join(errors) + " | " + detail)
                hard.extend(errors)
            cases.append(
                {
                    "id": case_id,
                    "product": product,
                    "message": turn["message"],
                    "status": status,
                    "errors": errors,
                    "elapsedMs": elapsed,
                    "snapshot": snap,
                    "sessionId": session_id,
                }
            )
        except Exception as exc:  # noqa: BLE001
            _fail(case_id, str(exc))
            hard.append(str(exc))
            cases.append(
                {
                    "id": case_id,
                    "product": product,
                    "status": "FAIL",
                    "errors": [str(exc)],
                    "sessionId": session_id,
                }
            )

    return cases, hard


def main() -> int:
    print(
        f"smoke_presentation_composer_conversation_live base={_BASE} "
        f"products={','.join(_PRODUCTS)}",
        flush=True,
    )
    cases: list[dict[str, Any]] = []
    hard: list[str] = []

    try:
        token = _token()
        agent_id = _agent(token)
        print(f"agent={agent_id}", flush=True)
    except Exception as exc:  # noqa: BLE001
        _fail("bootstrap", str(exc))
        return 1

    for product in _PRODUCTS:
        product_cases, product_hard = _run_product(token, agent_id, product)
        cases.extend(product_cases)
        hard.extend(product_hard)

    evidence = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "baseUrl": _BASE,
        "products": _PRODUCTS,
        "cases": cases,
        "hardFailures": hard,
        "pass": not hard,
    }
    out_path = Path(_OUT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nevidence={out_path} pass={evidence['pass']}", flush=True)
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        _fail("http", str(exc))
        raise SystemExit(1) from exc
