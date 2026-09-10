#!/usr/bin/env python3
"""D4 — superfícies STREAM + SIMULATE do residual path→display.

Aceite mínimo (remaining_debt D4):
  - 1 caso SSE stream com assert de stackPresentationPlan / labels
  - 1 caso admin simulate (sandbox) com assert de presentation/labels
  - sem vazamento técnico EN de operationId/summary cru

Uso:
  cd minha-delpi-ai-api
  SMOKE_BASE_URL=http://localhost \\
    PYTHONPATH=. .venv/bin/python -u scripts/smoke_residual_path_display_stream_simulate.py
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
_ADMIN = os.environ.get("SMOKE_AI_PREFIX", "/apps/minha-delpi-ai/api").strip()
_STOCK = os.environ.get("SMOKE_STOCK_CODE", "10080001").strip()
_TIMEOUT = float(os.environ.get("SMOKE_HTTP_TIMEOUT", "420"))
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/testing/evidence/residual_path_display_stream_simulate.json",
).strip()

_failed = 0


def _ok(label: str, detail: str = "") -> None:
    print(f"PASS  {label}" + (f" — {detail}" if detail else ""), flush=True)


def _fail(label: str, detail: str) -> None:
    global _failed
    _failed += 1
    print(f"FAIL  {label} — {detail}", flush=True)


def _http(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 120,
    accept: str = "application/json",
) -> Any:
    headers = {"Accept": accept}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        if accept == "text/event-stream":
            return raw
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


def _session(token: str, agent_id: str) -> str:
    payload = _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions",
        token=token,
        body={"agentId": agent_id, "title": "smoke-residual-d4-stream-simulate"},
    )
    sid = (payload or {}).get("id") or (payload or {}).get("sessionId")
    if not sid:
        raise RuntimeError(f"session failed: {payload}")
    return str(sid)


def _parse_sse(raw: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    current_event = "message"
    data_lines: list[str] = []

    def _flush() -> None:
        nonlocal current_event, data_lines
        if not data_lines:
            current_event = "message"
            return
        try:
            payload = json.loads("\n".join(data_lines))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            events.append((current_event, payload))
        current_event = "message"
        data_lines = []

    for line in raw.splitlines():
        if line.startswith("event:"):
            _flush()
            current_event = line[6:].strip() or "message"
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
        elif not line.strip():
            _flush()
    _flush()
    return events


def _walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _display_snapshot(payload: Any) -> dict[str, Any]:
    plans = 0
    tables = 0
    titles: list[str] = []
    route_title_keys: list[str] = []
    labels: list[str] = []
    path_leaks: list[str] = []

    for node in _walk(payload):
        if not isinstance(node, dict):
            continue
        if node.get("type") == "table" and (node.get("rows") or node.get("columns")):
            tables += 1
        if "tablePresentation" in node and isinstance(node.get("tablePresentation"), dict):
            tables += 1
        plan = node.get("stackPresentationPlan")
        if isinstance(plan, dict):
            plans += 1
            for key in ("resolvedRouteTitle", "sectionTitle", "title"):
                value = plan.get(key)
                if isinstance(value, str) and value.strip():
                    titles.append(value.strip())
            route_titles = plan.get("routeTitles")
            if isinstance(route_titles, dict):
                route_title_keys.extend(str(k) for k in route_titles.keys())
                titles.extend(str(v).strip() for v in route_titles.values() if str(v).strip())
        for key in ("title", "summary", "actionSummary", "routeTitle", "label"):
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                labels.append(value.strip())

    blob = "\n".join(titles + labels)
    lowered = blob.casefold()
    for leak in (
        "get_product_stock",
        "get product stock",
        "operationid",
        "customers —",
        "suppliers —",
        "/products/{code}/stock",
    ):
        if leak in lowered:
            path_leaks.append(leak)

    return {
        "plans": plans,
        "tables": tables,
        "titles_sample": titles[:8],
        "labels_sample": labels[:8],
        "plan_routeTitles_keys": sorted(set(route_title_keys))[:12],
        "path_leaks": path_leaks,
        "ok": plans >= 1 and tables >= 1 and not path_leaks,
    }


def _stream_stock(token: str, session_id: str, message: str) -> dict[str, Any]:
    raw = _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions/{session_id}/messages/stream",
        token=token,
        body={"message": message, "responseMode": "normal"},
        timeout=_TIMEOUT,
        accept="text/event-stream",
    )
    events = _parse_sse(str(raw))
    done = next((payload for name, payload in reversed(events) if name == "done"), {})
    snap = _display_snapshot(done)
    answer = str(done.get("answer") or "")
    return {
        "event_count": len(events),
        "has_done": bool(done),
        "answer_len": len(answer),
        "answer_preview": answer[:240],
        "tool_calls": len(done.get("toolCalls") or []),
        **snap,
    }


def _simulate_stock(token: str, agent_id: str, message: str) -> dict[str, Any]:
    payload = _http(
        "POST",
        f"{_BASE}{_ADMIN}/admin/agent/simulate",
        token=token,
        body={
            "question": message,
            "agentId": agent_id,
            "executeToolsInSandbox": True,
            "generateAnswer": False,
        },
        timeout=_TIMEOUT,
    )
    planned = (payload or {}).get("plannedToolCalls") or []
    snap = _display_snapshot(payload)
    # Simulate may put presentation only on executed tool metadata.
    if not snap["ok"]:
        snap = _display_snapshot({"toolCalls": planned})
        snap["source"] = "plannedToolCalls"
    else:
        snap["source"] = "simulate_root"
    return {
        "has_answer_preview": bool((payload or {}).get("answerPreview")),
        "planned_tool_count": len(planned),
        "tools_executed": bool(
            ((payload or {}).get("debugContext") or {}).get("toolsExecuted")
        ),
        **snap,
    }


def main() -> int:
    print(
        f"smoke_residual_path_display_stream_simulate base={_BASE} stock={_STOCK}",
        flush=True,
    )
    evidence: dict[str, Any] = {
        "stage": "D4_stream_simulate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stock_code": _STOCK,
        "cases": {},
        "SURFACES": {"STREAM": "FAIL", "SIMULATE": "FAIL"},
    }
    message = f"Consulte o estoque do produto {_STOCK}."

    try:
        token = _token()
        agent_id = _agent(token)
        evidence["agentId"] = agent_id
        _ok("bootstrap", f"agent={agent_id}")
    except Exception as exc:  # noqa: BLE001
        _fail("bootstrap", str(exc))
        return 1

    # --- STREAM ---
    try:
        session_id = _session(token, agent_id)
        evidence["sessionId"] = session_id
        started = time.perf_counter()
        stream_case = _stream_stock(token, session_id, message)
        stream_case["elapsed_s"] = round(time.perf_counter() - started, 2)
        evidence["cases"]["STREAM_stock"] = stream_case
        if not stream_case.get("has_done"):
            _fail("STREAM_stock", "done event missing")
        elif not stream_case.get("ok"):
            _fail(
                "STREAM_stock",
                f"plans={stream_case.get('plans')} tables={stream_case.get('tables')} "
                f"leaks={stream_case.get('path_leaks')}",
            )
        else:
            _ok(
                "STREAM_stock",
                f"plans={stream_case['plans']} tables={stream_case['tables']} "
                f"ms={stream_case['elapsed_s']}",
            )
            evidence["SURFACES"]["STREAM"] = "PASS"
    except Exception as exc:  # noqa: BLE001
        _fail("STREAM_stock", str(exc))
        evidence["cases"]["STREAM_stock"] = {"ok": False, "error": str(exc)}

    # --- SIMULATE ---
    try:
        started = time.perf_counter()
        sim_case = _simulate_stock(token, agent_id, message)
        sim_case["elapsed_s"] = round(time.perf_counter() - started, 2)
        evidence["cases"]["SIMULATE_stock"] = sim_case
        if not sim_case.get("tools_executed") and not sim_case.get("planned_tool_count"):
            _fail("SIMULATE_stock", "no planned/executed tools")
        elif not sim_case.get("ok"):
            _fail(
                "SIMULATE_stock",
                f"plans={sim_case.get('plans')} tables={sim_case.get('tables')} "
                f"leaks={sim_case.get('path_leaks')} executed={sim_case.get('tools_executed')}",
            )
        else:
            _ok(
                "SIMULATE_stock",
                f"plans={sim_case['plans']} tables={sim_case['tables']} "
                f"executed={sim_case['tools_executed']} ms={sim_case['elapsed_s']}",
            )
            evidence["SURFACES"]["SIMULATE"] = "PASS"
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        _fail("SIMULATE_stock", f"HTTP {exc.code}: {body[:240]}")
        evidence["cases"]["SIMULATE_stock"] = {
            "ok": False,
            "http": exc.code,
            "error": body[:400],
        }
    except Exception as exc:  # noqa: BLE001
        _fail("SIMULATE_stock", str(exc))
        evidence["cases"]["SIMULATE_stock"] = {"ok": False, "error": str(exc)}

    evidence["pass"] = (
        evidence["SURFACES"]["STREAM"] == "PASS"
        and evidence["SURFACES"]["SIMULATE"] == "PASS"
    )
    out_path = Path(_OUT)
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parents[1] / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nevidence={out_path} pass={evidence['pass']}", flush=True)
    return 0 if evidence["pass"] and _failed == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        _fail("http", str(exc))
        raise SystemExit(1) from exc
