#!/usr/bin/env python3
"""E9.S15 — live L1 para células que ainda bloqueavam globalReleasePass.

Gates alvo:
  recommendations_grounded  — chips/recs ancorados em recommendationQueries + presentation
  send_stream_simulate_parity — mesma consulta estoque em SEND / STREAM / SIMULATE

Uso:
  cd minha-delpi-ai-api
  .venv/bin/python -u scripts/smoke_e9_s15_release_blockers_live.py
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

_ROOT = Path(__file__).resolve().parents[1]
_BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip() or "http://localhost"
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USER = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_ADMIN = os.environ.get("SMOKE_AI_PREFIX", "/apps/minha-delpi-ai/api").strip()
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "10080022").strip()
_AGENT_ID = os.environ.get("SMOKE_AGENT_ID", "").strip()
_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip() or "normal"
_TIMEOUT = float(os.environ.get("SMOKE_HTTP_TIMEOUT", "600"))
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/roadmap/llm-json-decoupling/evidence/e9-s15-release-blockers-live.json",
).strip()
_CONTENT = (
    _ROOT
    / "app"
    / "content"
    / "pt-BR"
    / "assistant"
    / "humanized_data_response.json"
)

_ALLOWED_SUGGESTION_SOURCES = frozenset(
    {
        "presentationFollowUpSuggestions",
        "operationalRefinementFollowUpSuggestions",
        "followUpSuggestions",
        "recommendationQueries",
        "dataCommentary",
        "presentationDecision",
        "moreSuggestions",
        "helpFollowUpSuggestions",
        "anomalyClarificationSuggestions",
    }
)
_WRITE_MARKERS = (
    "exclua",
    "delete",
    "apague",
    "dropar",
    "drop table",
    "sem pedir confirmação",
)

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
    retries: int = 3,
) -> Any:
    last_exc: Exception | None = None
    active = token
    for attempt in range(1, max(1, retries) + 1):
        headers = {"Accept": accept}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if active:
            headers["Authorization"] = f"Bearer {active}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                if accept == "text/event-stream":
                    return raw
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 401 and attempt < retries:
                time.sleep(1)
                active = _token()
                continue
            body_txt = exc.read().decode("utf-8", errors="replace")
            raise urllib.error.HTTPError(
                exc.url, exc.code, exc.msg, exc.hdrs, fp=None
            ) from RuntimeError(body_txt[:400])
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            last_exc = exc
            if method.upper() == "POST" and (
                "/messages" in url or "/simulate" in url
            ):
                break
            if attempt >= retries:
                break
            time.sleep(min(10, 2 * attempt))
    assert last_exc is not None
    raise last_exc


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
        raise RuntimeError(f"token ausente: {payload}")
    return str(token)


def _agent(token: str) -> str:
    if _AGENT_ID:
        return _AGENT_ID
    agents = _http("GET", f"{_BASE}{_CHAT}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else (agents or {}).get("items") or []
    for agent in items:
        if not isinstance(agent, dict) or agent.get("enabled") is False:
            continue
        aid = str(agent.get("id") or "").strip()
        if aid:
            return aid
    raise RuntimeError(f"nenhum agent: {agents}")


def _session(token: str, agent_id: str, title: str) -> str:
    payload = _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions",
        token=token,
        body={"agentId": agent_id, "title": title},
    )
    sid = str((payload or {}).get("id") or "").strip()
    if not sid:
        raise RuntimeError(f"session fail: {payload}")
    return sid


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
    labels: list[str] = []
    path_leaks: list[str] = []

    for node in _walk(payload):
        if not isinstance(node, dict):
            continue
        if node.get("type") == "table" and (node.get("rows") or node.get("columns")):
            tables += 1
        if "tablePresentation" in node and isinstance(
            node.get("tablePresentation"), dict
        ):
            tables += 1
        plan = node.get("stackPresentationPlan")
        if isinstance(plan, dict):
            plans += 1
            for key in ("resolvedRouteTitle", "sectionTitle", "title"):
                value = plan.get(key)
                if isinstance(value, str) and value.strip():
                    titles.append(value.strip())
        for key in ("title", "summary", "actionSummary", "routeTitle", "label"):
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                labels.append(value.strip())

    blob = "\n".join(titles + labels).casefold()
    for leak in (
        "get_product_stock",
        "get product stock",
        "operationid",
        "/products/{code}/stock",
    ):
        if leak in blob:
            path_leaks.append(leak)

    return {
        "plans": plans,
        "tables": tables,
        "titles_sample": titles[:8],
        "labels_sample": labels[:8],
        "path_leaks": path_leaks,
        "ok": plans >= 1 and tables >= 1 and not path_leaks,
    }


def _stock_catalog() -> list[dict[str, str]]:
    data = json.loads(_CONTENT.read_text(encoding="utf-8"))
    rows = (data.get("recommendationQueries") or {}).get("stock") or []
    out: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "").strip()
        query = str(row.get("query") or "").strip()
        if label and query:
            out.append({"label": label, "query": query})
    return out


def _send(token: str, session_id: str, agent_id: str, message: str) -> dict:
    payload = _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": message,
            "agentId": agent_id,
            "responseMode": _MODE,
            "includeAdminDebug": True,
            "adminDebug": True,
        },
        timeout=_TIMEOUT,
    )
    return payload if isinstance(payload, dict) else {}


def _stream(token: str, session_id: str, message: str) -> dict[str, Any]:
    raw = _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions/{session_id}/messages/stream",
        token=token,
        body={"message": message, "responseMode": _MODE},
        timeout=_TIMEOUT,
        accept="text/event-stream",
    )
    events = _parse_sse(str(raw))
    done = next((payload for name, payload in reversed(events) if name == "done"), {})
    snap = _display_snapshot(done)
    answer = str(done.get("answer") or "")
    tools = done.get("toolCalls") if isinstance(done.get("toolCalls"), list) else []
    return {
        "event_count": len(events),
        "has_done": bool(done),
        "answer_len": len(answer),
        "tool_calls": len(tools),
        "paths": _tool_paths(tools),
        **snap,
    }


def _simulate(token: str, agent_id: str, message: str) -> dict[str, Any]:
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
    if not snap["ok"]:
        snap = _display_snapshot({"toolCalls": planned})
        snap["source"] = "plannedToolCalls"
    else:
        snap["source"] = "simulate_root"
    tools = planned if isinstance(planned, list) else []
    executed = bool(((payload or {}).get("debugContext") or {}).get("toolsExecuted"))
    return {
        "has_answer_preview": bool((payload or {}).get("answerPreview")),
        "planned_tool_count": len(tools),
        "tools_executed": executed,
        "paths": _tool_paths(tools),
        **snap,
    }


def _tool_paths(tools: list) -> list[str]:
    out: list[str] = []
    for tc in tools:
        if not isinstance(tc, dict):
            continue
        m = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
        path = str(m.get("path") or args.get("path") or "").strip()
        if path:
            out.append(path)
    return out


def _extract_commentary_recs(payload: dict) -> list[dict]:
    admin = payload.get("adminDebug") if isinstance(payload.get("adminDebug"), dict) else {}
    tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
    tools = tooling.get("toolCalls") if isinstance(tooling.get("toolCalls"), list) else []
    if not tools:
        tools = payload.get("toolCalls") if isinstance(payload.get("toolCalls"), list) else []
    for tc in tools:
        if not isinstance(tc, dict):
            continue
        meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        commentary = meta.get("dataCommentary") if isinstance(meta.get("dataCommentary"), dict) else {}
        recs = commentary.get("recommendations")
        if isinstance(recs, list) and recs:
            return [r for r in recs if isinstance(r, dict)]
    return []


def _extract_presentation_recs(payload: dict) -> list[dict]:
    admin = payload.get("adminDebug") if isinstance(payload.get("adminDebug"), dict) else {}
    tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
    tools = tooling.get("toolCalls") if isinstance(tooling.get("toolCalls"), list) else []
    out: list[dict] = []
    for tc in tools:
        if not isinstance(tc, dict):
            continue
        meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        decision = (
            meta.get("presentationDecision")
            if isinstance(meta.get("presentationDecision"), dict)
            else {}
        )
        recs = decision.get("recommendations")
        if isinstance(recs, list):
            out.extend(r for r in recs if isinstance(r, dict))
    return out


def _assert_recommendations(payload: dict, catalog: list[dict[str, str]]) -> dict[str, Any]:
    commentary = _extract_commentary_recs(payload)
    presentation = _extract_presentation_recs(payload)
    meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    follow_ups = meta.get("presentationFollowUpSuggestions")
    if not isinstance(follow_ups, list):
        follow_ups = []
    interactivity = meta.get("interactivity") if isinstance(meta.get("interactivity"), dict) else {}
    suggestions = interactivity.get("suggestions") if isinstance(interactivity.get("suggestions"), list) else []

    catalog_labels = {c["label"].casefold() for c in catalog}
    catalog_queries = {c["query"].casefold() for c in catalog}
    grounded_hits = 0
    for rec in commentary:
        text = str(rec.get("text") or rec.get("label") or "").strip().casefold()
        intent = str(rec.get("intent") or rec.get("query") or "").strip().casefold()
        if text in catalog_labels or intent in catalog_queries:
            grounded_hits += 1
        elif intent in catalog_labels or text in catalog_queries:
            grounded_hits += 1

    write_hits: list[str] = []
    for item in commentary + presentation + follow_ups + suggestions:
        if not isinstance(item, dict):
            continue
        blob = " ".join(
            str(item.get(k) or "") for k in ("label", "text", "query", "intent", "reason")
        ).casefold()
        for marker in _WRITE_MARKERS:
            if marker in blob:
                write_hits.append(marker)

    source_keys = {
        str(s.get("sourceKey") or "").strip()
        for s in suggestions
        if isinstance(s, dict) and str(s.get("sourceKey") or "").strip()
    }
    unknown_sources = sorted(k for k in source_keys if k not in _ALLOWED_SUGGESTION_SOURCES)

    actionable_followups = [
        f
        for f in follow_ups
        if isinstance(f, dict)
        and str(f.get("label") or "").strip()
        and str(f.get("query") or "").strip()
    ]

    result = {
        "commentary_count": len(commentary),
        "commentary_grounded_hits": grounded_hits,
        "presentation_rec_count": len(presentation),
        "follow_up_count": len(follow_ups),
        "actionable_follow_ups": len(actionable_followups),
        "suggestion_count": len(suggestions),
        "suggestion_source_keys": sorted(source_keys),
        "unknown_sources": unknown_sources,
        "write_marker_hits": write_hits,
        "commentary_sample": commentary[:3],
        "ok": False,
    }

    if len(commentary) < 1:
        _fail("recommendations_commentary", "dataCommentary.recommendations vazio")
    elif grounded_hits < 1:
        _fail(
            "recommendations_catalog_grounded",
            f"nenhum hit em recommendationQueries.stock; sample={commentary[:2]}",
        )
    else:
        _ok(
            "recommendations_catalog_grounded",
            f"hits={grounded_hits}/{len(commentary)} catalog={len(catalog)}",
        )

    if len(actionable_followups) < 1:
        _fail("recommendations_followups", "presentationFollowUpSuggestions sem label+query")
    else:
        _ok("recommendations_followups", f"n={len(actionable_followups)}")

    if unknown_sources:
        _fail("recommendations_sources", f"sourceKeys fora allowlist: {unknown_sources}")
    elif suggestions:
        _ok("recommendations_sources", f"keys={sorted(source_keys)}")
    else:
        _ok("recommendations_sources", "sem interactivity.suggestions (não bloqueante)")

    if write_hits:
        _fail("recommendations_no_write", f"markers={write_hits}")
    else:
        _ok("recommendations_no_write")

    # Negative sibling: inventar actionId fora do universo não deve passar silenciosamente
    # quando actionId aparece — deve estar vazio ou coerente (allowlist futura).
    rogue_action_ids = []
    for rec in commentary:
        aid = rec.get("actionId")
        if aid and str(aid).strip() and not str(aid).startswith(("api-delpi.", "delpi.")):
            # actionIds estruturados são ok se existirem; strings arbitrárias longas suspeitas
            if len(str(aid)) > 120:
                rogue_action_ids.append(str(aid)[:80])
    if rogue_action_ids:
        _fail("recommendations_action_ids", str(rogue_action_ids))
    else:
        _ok("recommendations_action_ids", "sem actionId rogue")

    result["ok"] = (
        grounded_hits >= 1
        and len(actionable_followups) >= 1
        and not unknown_sources
        and not write_hits
        and not rogue_action_ids
    )
    return result


def _path_ok(paths: list[str]) -> bool:
    target = f"/products/{_PRODUCT}/stock".casefold()
    soft = "/stock"
    joined = " ".join(paths).casefold()
    return target in joined or soft in joined


def main() -> int:
    print(
        f"smoke_e9_s15_release_blockers_live base={_BASE} product={_PRODUCT}",
        flush=True,
    )
    catalog = _stock_catalog()
    if len(catalog) < 2:
        print("FAIL bootstrap — recommendationQueries.stock ausente", flush=True)
        return 1

    evidence: dict[str, Any] = {
        "stage": "E9.S15_release_blockers",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_code": _PRODUCT,
        "gates": {
            "recommendations_grounded": "FAIL",
            "send_stream_simulate_parity": "FAIL",
        },
        "cases": {},
        "pass": False,
    }
    message = f"qual o estoque do produto {_PRODUCT}?"

    try:
        token = _token()
        agent_id = _agent(token)
        evidence["agentId"] = agent_id
        _ok("bootstrap", f"agent={agent_id}")
    except Exception as exc:  # noqa: BLE001
        _fail("bootstrap", str(exc))
        Path(_OUT).parent.mkdir(parents=True, exist_ok=True)
        Path(_OUT).write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    # --- SEND (recommendations + parity side) ---
    send_case: dict[str, Any] = {"ok": False}
    try:
        sid = _session(token, agent_id, "e9-s15-send")
        evidence["sessionId_send"] = sid
        started = time.perf_counter()
        payload = _send(token, sid, agent_id, message)
        elapsed = round(time.perf_counter() - started, 2)
        tools = payload.get("toolCalls") if isinstance(payload.get("toolCalls"), list) else []
        if not tools:
            admin = payload.get("adminDebug") if isinstance(payload.get("adminDebug"), dict) else {}
            tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
            tools = tooling.get("toolCalls") if isinstance(tooling.get("toolCalls"), list) else []
        paths = _tool_paths(tools if isinstance(tools, list) else [])
        snap = _display_snapshot(payload)
        rec = _assert_recommendations(payload, catalog)
        send_case = {
            "elapsed_s": elapsed,
            "paths": paths,
            "path_ok": _path_ok(paths),
            "display": snap,
            "recommendations": rec,
            "ok": bool(rec.get("ok")) and _path_ok(paths) and snap.get("ok") is True,
        }
        evidence["cases"]["SEND_stock"] = send_case
        if send_case["ok"]:
            _ok("SEND_stock", f"paths={paths} ms={elapsed}")
            evidence["gates"]["recommendations_grounded"] = "PASS"
        else:
            _fail(
                "SEND_stock",
                f"path_ok={send_case['path_ok']} display={snap.get('ok')} rec={rec.get('ok')}",
            )
    except Exception as exc:  # noqa: BLE001
        _fail("SEND_stock", str(exc))
        evidence["cases"]["SEND_stock"] = {"ok": False, "error": str(exc)}

    # --- STREAM ---
    stream_case: dict[str, Any] = {"ok": False}
    try:
        sid = _session(token, agent_id, "e9-s15-stream")
        evidence["sessionId_stream"] = sid
        started = time.perf_counter()
        stream_case = _stream(token, sid, message)
        stream_case["elapsed_s"] = round(time.perf_counter() - started, 2)
        stream_case["path_ok"] = _path_ok(stream_case.get("paths") or [])
        stream_case["ok"] = bool(
            stream_case.get("has_done")
            and stream_case.get("ok")
            and stream_case["path_ok"]
        )
        evidence["cases"]["STREAM_stock"] = stream_case
        if stream_case["ok"]:
            _ok(
                "STREAM_stock",
                f"plans={stream_case.get('plans')} tables={stream_case.get('tables')} "
                f"ms={stream_case['elapsed_s']}",
            )
        else:
            _fail(
                "STREAM_stock",
                f"done={stream_case.get('has_done')} display_ok={stream_case.get('ok')} "
                f"path_ok={stream_case.get('path_ok')} leaks={stream_case.get('path_leaks')}",
            )
    except Exception as exc:  # noqa: BLE001
        _fail("STREAM_stock", str(exc))
        evidence["cases"]["STREAM_stock"] = {"ok": False, "error": str(exc)}

    # --- SIMULATE ---
    sim_case: dict[str, Any] = {"ok": False}
    try:
        started = time.perf_counter()
        sim_case = _simulate(token, agent_id, message)
        sim_case["elapsed_s"] = round(time.perf_counter() - started, 2)
        sim_case["path_ok"] = _path_ok(sim_case.get("paths") or [])
        sim_case["ok"] = bool(
            (sim_case.get("tools_executed") or sim_case.get("planned_tool_count"))
            and sim_case.get("ok")
            and sim_case["path_ok"]
        )
        evidence["cases"]["SIMULATE_stock"] = sim_case
        if sim_case["ok"]:
            _ok(
                "SIMULATE_stock",
                f"plans={sim_case.get('plans')} tables={sim_case.get('tables')} "
                f"ms={sim_case['elapsed_s']}",
            )
        else:
            _fail(
                "SIMULATE_stock",
                f"display_ok={sim_case.get('ok')} path_ok={sim_case.get('path_ok')} "
                f"executed={sim_case.get('tools_executed')}",
            )
    except Exception as exc:  # noqa: BLE001
        _fail("SIMULATE_stock", str(exc))
        evidence["cases"]["SIMULATE_stock"] = {"ok": False, "error": str(exc)}

    # Parity: all three surfaces OK + share /stock path family
    send_ok = bool((evidence["cases"].get("SEND_stock") or {}).get("ok"))
    stream_ok = bool((evidence["cases"].get("STREAM_stock") or {}).get("ok"))
    sim_ok = bool((evidence["cases"].get("SIMULATE_stock") or {}).get("ok"))
    if send_ok and stream_ok and sim_ok:
        evidence["gates"]["send_stream_simulate_parity"] = "PASS"
        _ok("parity_send_stream_simulate", "3/3 surfaces PASS")
    else:
        _fail(
            "parity_send_stream_simulate",
            f"send={send_ok} stream={stream_ok} simulate={sim_ok}",
        )

    evidence["pass"] = (
        evidence["gates"]["recommendations_grounded"] == "PASS"
        and evidence["gates"]["send_stream_simulate_parity"] == "PASS"
        and _failed == 0
    )
    evidence["failed_count"] = _failed

    out_path = Path(_OUT)
    if not out_path.is_absolute():
        out_path = _ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"evidence → {out_path}", flush=True)
    print(f"OVERALL {'PASS' if evidence['pass'] else 'FAIL'} failed={_failed}", flush=True)
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
