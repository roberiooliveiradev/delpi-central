#!/usr/bin/env python3
"""Live smoke — only the C4 conversation texts (seed + follow-up).

Evaluates L1–L4 lightly against metadata (not just structural kinds).
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
_PRODUCT = os.environ.get(
    "SMOKE_PA_CODE", os.environ.get("SMOKE_PRODUCT_CODE", "90260149")
).strip()
_AGENT_ID = os.environ.get("SMOKE_AGENT_ID", "").strip()
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/testing/evidence/chat-c4-conversation-live.json",
).strip()

SEED = f"estoque e descrição do produto {_PRODUCT}"
FOLLOWUP = (
    "Agora completa: inclui também a estrutura e um comentário se o estoque "
    "cobre demanda típica. Quero visão consolidada (prosa + tabela/árvore), "
    "não só um bloco."
)


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    retries: int = 3,
    timeout: int = 600,
) -> Any:
    last_exc: Exception | None = None
    active_token = token
    for attempt in range(1, max(1, retries) + 1):
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if active_token:
            headers["Authorization"] = f"Bearer {active_token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 401 and attempt < retries:
                print(
                    f"retry {attempt}/{retries} after HTTP 401; renew token",
                    flush=True,
                )
                active_token = _token()
                time.sleep(1)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            last_exc = exc
            # Não reenvia POST de mensagem após timeout: Flask dev é single-thread
            # e o request original ainda pode estar em andamento.
            if method.upper() == "POST" and "/messages" in url:
                break
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


def _tree_ok(meta: dict, payload: dict | None = None) -> tuple[bool, str]:
    tool_calls = []
    if isinstance(payload, dict):
        tool_calls = payload.get("toolCalls") or []
    if not tool_calls and isinstance(meta, dict):
        tool_calls = meta.get("toolCalls") or []
    for tc in tool_calls:
        m = tc.get("metadata") if isinstance(tc, dict) else None
        if not isinstance(m, dict):
            continue
        tree = m.get("treePresentation")
        if not isinstance(tree, dict):
            continue
        root = tree.get("root") if isinstance(tree.get("root"), dict) else {}
        children = root.get("children") or []
        if not children:
            continue
        bad = [
            c
            for c in children
            if isinstance(c, dict)
            and (
                str(c.get("id") or "") in {"", "unknown"}
                or str(c.get("label") or "") in {"", "—"}
            )
        ]
        if bad:
            return False, f"tree has {len(bad)}/{len(children)} unknown/dash children"
        return True, f"tree ok ({len(children)} children)"
    return True, "no tree (ok if table-only)"


_INLINE_MD_BLOCK_RE = re.compile(
    r"(?<=[^\n#])[ \t]*#{1,6}[ \t]+\S|(?<=[.!?:;])[ \t]+(?:[-*+][ \t]+\S|\d+\.[ \t]+\S)"
)


def _markdown_structure_ok(content: str) -> tuple[bool, str]:
    """L3: ATX headings / list markers must not sit mid-line after non-whitespace."""
    text = str(content or "")
    # Ignore fenced code when scanning.
    scrubbed = re.sub(r"```[\s\S]*?```|~~~[\s\S]*?~~~", "", text)
    match = _INLINE_MD_BLOCK_RE.search(scrubbed)
    if match:
        start = max(0, match.start() - 24)
        end = min(len(scrubbed), match.end() + 24)
        return False, f"inline markdown block near {scrubbed[start:end]!r}"
    return True, "markdown block structure ok"


def _dashboard_structure_dup(meta: dict, payload: dict | None = None) -> tuple[bool, str]:
    tool_calls = []
    if isinstance(payload, dict):
        tool_calls = payload.get("toolCalls") or []
    if not tool_calls and isinstance(meta, dict):
        tool_calls = meta.get("toolCalls") or []
    for tc in tool_calls:
        m = tc.get("metadata") if isinstance(tc, dict) else None
        if not isinstance(m, dict):
            continue
        dash = m.get("dashboardPresentation")
        if not isinstance(dash, dict):
            continue
        panels = dash.get("panels") or []
        tree_n = 0
        table_n = 0
        for panel in panels:
            if not isinstance(panel, dict):
                continue
            title = str(panel.get("title") or "").lower()
            pid = str(panel.get("id") or "").lower()
            pres = panel.get("presentation") if isinstance(panel.get("presentation"), dict) else {}
            is_struct = pid == "structure" or "estrutura" in title or "bom" in title
            if not is_struct:
                continue
            if pres.get("type") == "tree":
                tree_n += 1
            if pres.get("type") == "table":
                table_n += 1
        if tree_n and table_n:
            return False, f"dashboard duplicates structure tree+table ({tree_n}/{table_n})"
    return True, "no structure duplication"


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
        body={"agentId": agent_id, "title": "smoke-c4-conversation"},
    )
    session_id = str((session or {}).get("id") or "").strip()
    if not session_id:
        print("FAIL create session", session, flush=True)
        return 1

    results: dict[str, Any] = {
        "sessionId": session_id,
        "agentId": agent_id,
        "productKind": "pa",
        "productCode": _PRODUCT,
        "routeFamily": "product",
        "turns": [],
    }
    failures: list[str] = []

    for label, message in (("seed", SEED), ("followup", FOLLOWUP)):
        print(f"--- {label}: {message}", flush=True)
        token = _token()  # turns longos estouram expires_in
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
        tree_ok, tree_msg = _tree_ok(meta, payload if isinstance(payload, dict) else None)
        dash_ok, dash_msg = _dashboard_structure_dup(
            meta, payload if isinstance(payload, dict) else None
        )
        md_ok, md_msg = _markdown_structure_ok(content)
        low = content.lower()
        turn = {
            "label": label,
            "wallMs": wall,
            "paths": paths,
            "proseChars": len(content.strip()),
            "tree": tree_msg,
            "dashboard": dash_msg,
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
            if not tree_ok:
                failures.append(f"L3 followup: {tree_msg}")
            if not dash_ok:
                failures.append(f"L3 followup: {dash_msg}")
            denies = (
                "não tenho o estoque",
                "nao tenho o estoque",
                "não trouxe a posição de estoque",
                "nao trouxe a posicao de estoque",
            )
            if any(d in low for d in denies):
                failures.append("L2 followup: prose denies stock presence")
            if "cobre" not in low and "estoque" not in low:
                failures.append("L4 followup: missing coverage/stock commentary")
            has_structure_path = any(
                "/analyser" in p or "/structure" in p for p in paths
            )
            if not has_structure_path:
                failures.append("L1 followup: missing structure/analyser")

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
    print("PASS L1–L4 (C4 conversation texts)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
