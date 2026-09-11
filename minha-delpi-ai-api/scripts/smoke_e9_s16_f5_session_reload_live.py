#!/usr/bin/env python3
"""E9.S16 — F5/session reload via API (superfície de persistência do chat).

Simula reload de sessão sem browser:
  1) SEND estoque
  2) GET /sessions/{id}/messages (reload do histórico persistido)
  3) FOLLOW-UP reconsulta o mesmo produto na mesma sessão
  4) Assert continuidade (mesmo product /stock após GET reload)

Uso:
  cd minha-delpi-ai-api
  .venv/bin/python -u scripts/smoke_e9_s16_f5_session_reload_live.py
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
    "docs/roadmap/llm-json-decoupling/evidence/e9-s16-f5-session-reload-live.json",
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


def _session(token: str, agent_id: str) -> str:
    payload = _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions",
        token=token,
        body={"agentId": agent_id, "title": "e9-s16-f5-reload"},
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


def _list_messages(token: str, session_id: str) -> list[dict]:
    payload = _http(
        "GET",
        f"{_BASE}{_CHAT}/sessions/{session_id}/messages?limit=50",
        token=token,
        timeout=120,
    )
    if isinstance(payload, list):
        return [m for m in payload if isinstance(m, dict)]
    if isinstance(payload, dict):
        items = payload.get("items") or payload.get("messages") or []
        if isinstance(items, list):
            return [m for m in items if isinstance(m, dict)]
    return []


def _tool_paths(payload: dict) -> list[str]:
    tools = payload.get("toolCalls") if isinstance(payload.get("toolCalls"), list) else []
    if not tools:
        admin = payload.get("adminDebug") if isinstance(payload.get("adminDebug"), dict) else {}
        tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
        tools = tooling.get("toolCalls") if isinstance(tooling.get("toolCalls"), list) else []
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


def _history_has_stock_tool(messages: list[dict]) -> bool:
    needle = f"/products/{_PRODUCT}/stock".casefold()
    for msg in messages:
        if str(msg.get("role") or "").lower() != "assistant":
            continue
        meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
        tools = meta.get("toolCalls") if isinstance(meta.get("toolCalls"), list) else []
        blob = json.dumps(tools, ensure_ascii=False).casefold()
        if needle in blob or "/stock" in blob:
            return True
    return False


def _followup_page(payload: dict) -> int | None:
    for path_key in ("toolCalls",):
        tools = payload.get(path_key)
        if not isinstance(tools, list):
            admin = payload.get("adminDebug") if isinstance(payload.get("adminDebug"), dict) else {}
            tooling = admin.get("tooling") if isinstance(admin.get("tooling"), dict) else {}
            tools = tooling.get("toolCalls") if isinstance(tooling.get("toolCalls"), list) else []
        for tc in tools or []:
            if not isinstance(tc, dict):
                continue
            args = tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {}
            params = args.get("parameters") if isinstance(args.get("parameters"), dict) else args
            if not isinstance(params, dict):
                continue
            for key in ("page", "pageNumber", "page_number"):
                if key in params:
                    try:
                        return int(params[key])
                    except (TypeError, ValueError):
                        pass
            meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
            req = meta.get("requestParameters") if isinstance(meta.get("requestParameters"), dict) else {}
            for key in ("page", "pageNumber", "page_number"):
                if key in req:
                    try:
                        return int(req[key])
                    except (TypeError, ValueError):
                        pass
    return None


def main() -> int:
    print(f"smoke_e9_s16_f5_session_reload_live base={_BASE} product={_PRODUCT}", flush=True)
    evidence: dict[str, Any] = {
        "stage": "E9.S16_f5_session_reload",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_code": _PRODUCT,
        "surface": "API_SESSION_RELOAD",
        "note": "Equivalente backend do F5: GET messages + follow-up na mesma sessão (sem Playwright/MFE).",
        "cases": {},
        "pass": False,
    }

    try:
        token = _token()
        agent_id = _agent(token)
        session_id = _session(token, agent_id)
        evidence["agentId"] = agent_id
        evidence["sessionId"] = session_id
        _ok("bootstrap", f"session={session_id}")
    except Exception as exc:  # noqa: BLE001
        _fail("bootstrap", str(exc))
        out = _ROOT / _OUT if not Path(_OUT).is_absolute() else Path(_OUT)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    seed_msg = f"qual o estoque do produto {_PRODUCT}?"
    try:
        started = time.perf_counter()
        seed = _send(token, session_id, agent_id, seed_msg)
        paths = _tool_paths(seed)
        seed_ok = any("/stock" in p.casefold() for p in paths)
        evidence["cases"]["SEED_stock"] = {
            "elapsed_s": round(time.perf_counter() - started, 2),
            "paths": paths,
            "ok": seed_ok,
        }
        if seed_ok:
            _ok("SEED_stock", f"paths={paths}")
        else:
            _fail("SEED_stock", f"paths={paths}")
    except Exception as exc:  # noqa: BLE001
        _fail("SEED_stock", str(exc))
        evidence["cases"]["SEED_stock"] = {"ok": False, "error": str(exc)}

    try:
        started = time.perf_counter()
        messages = _list_messages(token, session_id)
        reload_ok = len(messages) >= 2 and _history_has_stock_tool(messages)
        evidence["cases"]["GET_messages_reload"] = {
            "elapsed_s": round(time.perf_counter() - started, 2),
            "message_count": len(messages),
            "has_stock_tool_in_history": _history_has_stock_tool(messages),
            "ok": reload_ok,
        }
        if reload_ok:
            _ok("GET_messages_reload", f"n={len(messages)}")
        else:
            _fail(
                "GET_messages_reload",
                f"n={len(messages)} stock_tool={_history_has_stock_tool(messages)}",
            )
    except Exception as exc:  # noqa: BLE001
        _fail("GET_messages_reload", str(exc))
        evidence["cases"]["GET_messages_reload"] = {"ok": False, "error": str(exc)}

    # Após GET reload: follow-up que reutiliza o produto do histórico (continuidade F5).
    # «próxima página» pode falhar sem rows no contexto; reconsulta do mesmo produto é o aceite canônico.
    follow_msg = "mostre de novo o estoque desse mesmo produto"
    try:
        started = time.perf_counter()
        follow = _send(token, session_id, agent_id, follow_msg)
        paths = _tool_paths(follow)
        blob = json.dumps(follow, ensure_ascii=False).casefold()
        path_ok = any(
            f"/products/{_PRODUCT}/stock".casefold() in p.casefold() or "/stock" in p.casefold()
            for p in paths
        ) or (
            f"/products/{_PRODUCT}/stock".casefold() in blob
            and "stock" in blob
        )
        product_ok = _PRODUCT in blob
        follow_ok = path_ok and product_ok
        evidence["cases"]["FOLLOWUP_same_product_after_reload"] = {
            "elapsed_s": round(time.perf_counter() - started, 2),
            "message": follow_msg,
            "paths": paths,
            "product_in_payload": product_ok,
            "ok": follow_ok,
        }
        if follow_ok:
            _ok("FOLLOWUP_same_product_after_reload", f"paths={paths}")
        else:
            _fail(
                "FOLLOWUP_same_product_after_reload",
                f"paths={paths} product_ok={product_ok}",
            )
    except Exception as exc:  # noqa: BLE001
        _fail("FOLLOWUP_same_product_after_reload", str(exc))
        evidence["cases"]["FOLLOWUP_same_product_after_reload"] = {
            "ok": False,
            "error": str(exc),
        }

    evidence["pass"] = (
        _failed == 0
        and bool((evidence["cases"].get("SEED_stock") or {}).get("ok"))
        and bool((evidence["cases"].get("GET_messages_reload") or {}).get("ok"))
        and bool((evidence["cases"].get("FOLLOWUP_same_product_after_reload") or {}).get("ok"))
    )
    evidence["failed_count"] = _failed
    out = _ROOT / _OUT if not Path(_OUT).is_absolute() else Path(_OUT)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"evidence → {out}", flush=True)
    print(f"OVERALL {'PASS' if evidence['pass'] else 'FAIL'} failed={_failed}", flush=True)
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
