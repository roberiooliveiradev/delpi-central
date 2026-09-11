#!/usr/bin/env python3
"""Live smoke — C5 MP conversation (stock + coverage/sales, no BOM required).

Evaluates L1–L4 lightly. Fixture: SMOKE_MP_CODE (default 10080022).
Does NOT require /structure.
"""

from __future__ import annotations
from smoke_credentials import require_smoke_credentials

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip() or "http://localhost"
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USER, _PASSWORD = require_smoke_credentials()
_CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip() or "normal"
_MP = os.environ.get("SMOKE_MP_CODE", "10080022").strip()
_AGENT_ID = os.environ.get("SMOKE_AGENT_ID", "").strip()
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/testing/evidence/chat-c5-mp-stock-followup-live.json",
).strip()

SEED = f"estoque e descrição do produto {_MP}"
FOLLOWUP = (
    f"Consulta de novo o estoque do produto {_MP} e um resumo de vendas/saídas "
    "recentes (tool de vendas ou movimentação). Comenta se o saldo cobre a "
    "demanda típica. Não use estrutura BOM — só estoque e vendas."
)

_INLINE_MD_BLOCK_RE = re.compile(
    r"(?<=[^\n#])[ \t]*#{1,6}[ \t]+\S|(?<=[.!?:;])[ \t]+(?:[-*+][ \t]+\S|\d+\.[ \t]+\S)"
)


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    retries: int = 3,
) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last_exc: Exception | None = None
    for attempt in range(1, max(1, retries) + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=420) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            last_exc = exc
            if attempt >= retries:
                break
            wait_s = min(30, 5 * attempt)
            print(
                f"retry {attempt}/{retries} after {type(exc).__name__}; sleep {wait_s}s",
                flush=True,
            )
            time.sleep(wait_s)
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


def _paths(meta: dict, payload: dict | None = None) -> list[str]:
    out: list[str] = []
    tool_calls = []
    if isinstance(payload, dict):
        tool_calls = payload.get("toolCalls") or []
    if not tool_calls and isinstance(meta, dict):
        tool_calls = meta.get("toolCalls") or []
    for tc in tool_calls:
        if not isinstance(tc, dict):
            continue
        m = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        path = str(m.get("path") or (tc.get("arguments") or {}).get("path") or "").strip()
        if path:
            out.append(path)
    return out


def _markdown_structure_ok(content: str) -> tuple[bool, str]:
    scrubbed = re.sub(r"```[\s\S]*?```|~~~[\s\S]*?~~~", "", str(content or ""))
    match = _INLINE_MD_BLOCK_RE.search(scrubbed)
    if match:
        start = max(0, match.start() - 24)
        end = min(len(scrubbed), match.end() + 24)
        return False, f"inline markdown block near {scrubbed[start:end]!r}"
    return True, "markdown block structure ok"


def _resolve_agent_id(token: str) -> str:
    if _AGENT_ID:
        return _AGENT_ID
    agents = _http_json("GET", f"{_BASE}{_CHAT}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else (agents or {}).get("items") or []
    for agent in items:
        if not isinstance(agent, dict):
            continue
        if agent.get("enabled") is False:
            continue
        aid = str(agent.get("id") or "").strip()
        if aid:
            return aid
    raise RuntimeError(f"nenhum agent disponível: {agents}")


def main() -> int:
    token = _token()
    agent_id = _resolve_agent_id(token)
    print(f"agent={agent_id}", flush=True)
    session = _http_json(
        "POST",
        f"{_BASE}{_CHAT}/sessions",
        token=token,
        body={"agentId": agent_id, "title": "smoke-c5-mp-stock"},
    )
    session_id = str((session or {}).get("id") or "").strip()
    if not session_id:
        print("FAIL create session", session, flush=True)
        return 1

    results: dict[str, Any] = {
        "sessionId": session_id,
        "agentId": agent_id,
        "productKind": "mp",
        "productCode": _MP,
        "routeFamily": "product",
        "turns": [],
    }
    failures: list[str] = []

    for label, message in (("seed", SEED), ("followup", FOLLOWUP)):
        print(f"--- {label}: {message}", flush=True)
        token = _token()
        t0 = time.time()
        try:
            payload = _http_json(
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
            )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"FAIL HTTP {exc.code}: {body[:400]}", flush=True)
            return 1
        wall = int((time.time() - t0) * 1000)
        msg = payload if isinstance(payload, dict) else {}
        nested = msg.get("message") if isinstance(msg.get("message"), dict) else None
        if nested:
            msg = nested
        meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
        if not meta and isinstance(payload, dict) and isinstance(payload.get("metadata"), dict):
            meta = payload["metadata"]
        content = ""
        for source in (msg, payload if isinstance(payload, dict) else {}):
            for key in ("content", "answer", "text"):
                if str(source.get(key) or "").strip():
                    content = str(source.get(key))
                    break
            if content:
                break
        paths = _paths(meta, payload if isinstance(payload, dict) else None)
        md_ok, md_msg = _markdown_structure_ok(content)
        low = content.lower()
        turn = {
            "label": label,
            "wallMs": wall,
            "paths": paths,
            "proseChars": len(content.strip()),
            "markdown": md_msg,
            "prosePreview": content.strip()[:280],
        }
        results["turns"].append(turn)
        print(json.dumps(turn, ensure_ascii=False, indent=2), flush=True)

        if not md_ok:
            failures.append(f"L3 {label}: {md_msg}")
        if label == "seed":
            if not any("/stock" in p for p in paths):
                failures.append("L1 seed: missing /stock path")
            if any("/summary" in p for p in paths) and not any("/stock" in p for p in paths):
                failures.append("L1 seed: /summary without /stock")
        if label == "followup":
            if not any("/stock" in p or "/sales" in p for p in paths):
                failures.append("L1 followup: missing /stock or /sales")
            # Structure is optional — do not require; only warn if seed lacked stock.
            denies = (
                "não tenho o estoque",
                "nao tenho o estoque",
                "não trouxe a posição de estoque",
                "nao trouxe a posicao de estoque",
            )
            if any(d in low for d in denies):
                failures.append("L2 followup: prose denies stock presence")
            if "cobre" not in low and "estoque" not in low and "venda" not in low:
                failures.append("L4 followup: missing coverage/stock/sales commentary")

    results["failures"] = failures
    results["passed"] = not failures
    out_path = _OUT if os.path.isabs(_OUT) else os.path.join(os.getcwd(), _OUT)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
    print("=" * 72, flush=True)
    print(f"evidence={out_path}", flush=True)
    if failures:
        print("FAIL_QUALITATIVO", flush=True)
        for item in failures:
            print(f"  - {item}", flush=True)
        return 1
    print("PASS L1–L4 (C5 MP stock/sales texts)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
