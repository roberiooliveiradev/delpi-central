#!/usr/bin/env python3
"""E10 — live: zero mapa lateral + domínio via catalog/inference.

Gates alvo:
  content_no_lateral_keys — assistant JSON sem pathMarkers/pathToken/pathContains/pathRules
  product_stock_domain    — SEND estoque → apiRouteDomain=product (+ path /stock)
  department_kpi_sibling  — SEND KPI comercial → apiRouteDomain=department_kpi
  unknown_safe_negative   — pedido sem action clara não explode; sem pathMarkers no debug

Uso:
  cd minha-delpi-ai-api
  .venv/bin/python -u scripts/smoke_e10_zero_lateral_path_maps_live.py
"""

from __future__ import annotations
from smoke_credentials import require_smoke_credentials

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
_USER, _PASSWORD = require_smoke_credentials()
_CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "10080022").strip()
_AGENT_ID = os.environ.get("SMOKE_AGENT_ID", "").strip()
_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip() or "normal"
_TIMEOUT = float(os.environ.get("SMOKE_HTTP_TIMEOUT", "600"))
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/roadmap/llm-json-decoupling/evidence/e10-zero-lateral-path-maps-live.json",
).strip()
_ASSISTANT = _ROOT / "app" / "content" / "pt-BR" / "assistant"

_FORBIDDEN_KEYS = frozenset(
    {
        "pathMarkers",
        "excludePathMarkers",
        "pathMarkersKey",
        "pathToken",
        "pathContains",
        "pathExactEnd",
        "pathSuffix",
        "pathContainsFromKey",
        "pathRules",
    }
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
    retries: int = 3,
) -> Any:
    last_exc: Exception | None = None
    active = token
    for attempt in range(1, max(1, retries) + 1):
        headers = {"Accept": "application/json"}
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
            if method.upper() == "POST" and "/messages" in url:
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


def _tool_calls(payload: dict) -> list[dict]:
    tools = payload.get("toolCalls") if isinstance(payload.get("toolCalls"), list) else []
    if tools:
        return [t for t in tools if isinstance(t, dict)]
    admin = payload.get("adminDebug") if isinstance(payload.get("adminDebug"), dict) else {}
    tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
    tools = tooling.get("toolCalls") if isinstance(tooling.get("toolCalls"), list) else []
    return [t for t in tools if isinstance(t, dict)]


def _tool_identities(payload: dict) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for tc in _tool_calls(payload):
        meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
        out.append(
            {
                "path": str(meta.get("path") or args.get("path") or "").strip(),
                "apiRouteDomain": str(
                    meta.get("apiRouteDomain") or meta.get("api_route_domain") or ""
                ).strip(),
                "operationId": str(
                    meta.get("operationId")
                    or args.get("operationId")
                    or tc.get("operationId")
                    or ""
                ).strip(),
                "actionId": str(
                    meta.get("actionId") or args.get("actionId") or tc.get("actionId") or ""
                ).strip(),
                "ok": str(meta.get("ok") if "ok" in meta else "").strip(),
            }
        )
    return out


def _content_forbidden_hits() -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for path in sorted(_ASSISTANT.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        found: list[str] = []

        def walk(node: object, cursor: str = "$") -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    key_s = str(key)
                    if key_s in _FORBIDDEN_KEYS or "PathMarkers" in key_s:
                        found.append(f"{cursor}.{key_s}")
                    walk(value, f"{cursor}.{key_s}")
            elif isinstance(node, list):
                for index, item in enumerate(node):
                    walk(item, f"{cursor}[{index}]")

        walk(payload)
        if found:
            hits[str(path.relative_to(_ASSISTANT))] = found
    return hits


def _debug_mentions_path_markers(payload: dict) -> bool:
    blob = json.dumps(payload, ensure_ascii=False)
    # authority residual no content seria vazamento; strings em gate/forbidden OK
    return '"pathMarkers"' in blob or '"pathToken"' in blob or '"pathRules"' in blob


def main() -> int:
    print(
        f"smoke_e10_zero_lateral_path_maps_live base={_BASE} product={_PRODUCT}",
        flush=True,
    )
    evidence: dict[str, Any] = {
        "stage": "E10_zero_lateral_path_maps_live",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_code": _PRODUCT,
        "cases": {},
        "pass": False,
    }

    # --- content gate (sem auth) ---
    hits = _content_forbidden_hits()
    content_ok = hits == {}
    evidence["cases"]["content_no_lateral_keys"] = {
        "ok": content_ok,
        "hit_files": sorted(hits.keys()),
        "hit_count": sum(len(v) for v in hits.values()),
    }
    if content_ok:
        _ok("content_no_lateral_keys", "0 forbidden keys")
    else:
        _fail("content_no_lateral_keys", f"hits={hits}")

    try:
        token = _token()
        agent_id = _agent(token)
        evidence["agentId"] = agent_id
        _ok("bootstrap", f"agent={agent_id}")
    except Exception as exc:  # noqa: BLE001
        _fail("bootstrap", str(exc))
        out = _ROOT / _OUT if not Path(_OUT).is_absolute() else Path(_OUT)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"evidence → {out}", flush=True)
        return 1

    # --- positive: product stock domain ---
    try:
        session_id = _session(token, agent_id, "e10-product-stock")
        started = time.perf_counter()
        payload = _send(
            token,
            session_id,
            agent_id,
            f"qual o estoque do produto {_PRODUCT}?",
        )
        identities = _tool_identities(payload)
        stock_hits = [
            item
            for item in identities
            if "/stock" in item["path"].casefold()
            and _PRODUCT in item["path"]
        ]
        domains = {item["apiRouteDomain"] for item in stock_hits if item["apiRouteDomain"]}
        domain_ok = any(d == "product" for d in domains) or (
            any(d.startswith("product") for d in domains) and bool(stock_hits)
        )
        path_ok = bool(stock_hits)
        case_ok = path_ok and domain_ok and not _debug_mentions_path_markers(payload)
        evidence["cases"]["product_stock_domain"] = {
            "elapsed_s": round(time.perf_counter() - started, 2),
            "sessionId": session_id,
            "identities": identities,
            "domains": sorted(domains),
            "ok": case_ok,
        }
        if case_ok:
            _ok("product_stock_domain", f"domains={sorted(domains)} paths={[i['path'] for i in stock_hits]}")
        else:
            _fail(
                "product_stock_domain",
                f"path_ok={path_ok} domain_ok={domain_ok} identities={identities}",
            )
    except Exception as exc:  # noqa: BLE001
        _fail("product_stock_domain", str(exc))
        evidence["cases"]["product_stock_domain"] = {"ok": False, "error": str(exc)}

    # --- sibling: department KPI ---
    try:
        session_id = _session(token, agent_id, "e10-department-kpi")
        started = time.perf_counter()
        payload = _send(
            token,
            session_id,
            agent_id,
            "qual a taxa de conversão comercial neste mês?",
        )
        identities = _tool_identities(payload)
        kpi_hits = [
            item
            for item in identities
            if "/commercial/" in item["path"].casefold()
            or "closing" in item["path"].casefold()
            or "closing" in item["operationId"].casefold()
            or item["apiRouteDomain"] == "department_kpi"
        ]
        domains = {item["apiRouteDomain"] for item in identities if item["apiRouteDomain"]}
        domain_ok = "department_kpi" in domains or any(
            item["apiRouteDomain"] == "department_kpi" for item in kpi_hits
        )
        path_ok = bool(kpi_hits) or any("/commercial/" in i["path"].casefold() for i in identities)
        case_ok = path_ok and domain_ok
        evidence["cases"]["department_kpi_sibling"] = {
            "elapsed_s": round(time.perf_counter() - started, 2),
            "sessionId": session_id,
            "identities": identities,
            "domains": sorted(domains),
            "ok": case_ok,
        }
        if case_ok:
            _ok(
                "department_kpi_sibling",
                f"domains={sorted(domains)} sample={[i['path'] for i in identities[:3]]}",
            )
        else:
            _fail(
                "department_kpi_sibling",
                f"path_ok={path_ok} domain_ok={domain_ok} identities={identities}",
            )
    except Exception as exc:  # noqa: BLE001
        _fail("department_kpi_sibling", str(exc))
        evidence["cases"]["department_kpi_sibling"] = {"ok": False, "error": str(exc)}

    # --- negative: unclear ask should not smuggle pathMarkers / should respond ---
    try:
        session_id = _session(token, agent_id, "e10-unknown-safe")
        started = time.perf_counter()
        payload = _send(
            token,
            session_id,
            agent_id,
            "xyzzy quux foobar sem sentido operacional 999?",
        )
        text = str(payload.get("content") or payload.get("message") or "").strip()
        admin = payload.get("adminDebug") if isinstance(payload.get("adminDebug"), dict) else {}
        has_reply = bool(text) or bool(admin) or "toolCalls" in payload
        no_markers = not _debug_mentions_path_markers(payload)
        case_ok = has_reply and no_markers
        evidence["cases"]["unknown_safe_negative"] = {
            "elapsed_s": round(time.perf_counter() - started, 2),
            "sessionId": session_id,
            "has_reply": has_reply,
            "no_path_map_keys_in_payload": no_markers,
            "content_preview": text[:180],
            "ok": case_ok,
        }
        if case_ok:
            _ok("unknown_safe_negative", f"reply_len={len(text)}")
        else:
            _fail(
                "unknown_safe_negative",
                f"has_reply={has_reply} no_markers={no_markers}",
            )
    except Exception as exc:  # noqa: BLE001
        _fail("unknown_safe_negative", str(exc))
        evidence["cases"]["unknown_safe_negative"] = {"ok": False, "error": str(exc)}

    evidence["pass"] = _failed == 0 and all(
        bool((evidence["cases"].get(name) or {}).get("ok"))
        for name in (
            "content_no_lateral_keys",
            "product_stock_domain",
            "department_kpi_sibling",
            "unknown_safe_negative",
        )
    )
    evidence["failed_count"] = _failed

    out = _ROOT / _OUT if not Path(_OUT).is_absolute() else Path(_OUT)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"evidence → {out}", flush=True)
    print(f"OVERALL={'PASS' if evidence['pass'] else 'FAIL'}", flush=True)
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
