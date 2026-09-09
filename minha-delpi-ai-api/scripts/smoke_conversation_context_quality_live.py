#!/usr/bin/env python3
"""Live harness E8 — Session A (default) or B–E via SMOKE_E8_FIXTURE.

Does not print PASS unless every requiredDimension is evidenced. Missing graders
stay INCONCLUSIVE (chat-ai-flow-families.md §1.1).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

_BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip() or "http://localhost"
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USER = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip() or "normal"
_MP = os.environ.get("SMOKE_MP_CODE", "10080055").strip()
_AGENT_ID = os.environ.get(
    "SMOKE_AGENT_ID", "b85edd53-2fd9-4e2f-ab17-92fd288f4f85"
).strip()
_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = Path(
    os.environ.get(
        "SMOKE_E8_FIXTURE",
        str(_ROOT / "tests/fixtures/chat_conversation_context_quality.json"),
    )
)
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/testing/evidence/chat-conversation-context-quality-live.json",
).strip()


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
            time.sleep(min(30, 5 * attempt))
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


def _action_ids(meta: dict, payload: dict | None) -> list[str]:
    out: list[str] = []
    tool_calls = []
    if isinstance(payload, dict):
        tool_calls = payload.get("toolCalls") or []
    if not tool_calls and isinstance(meta, dict):
        tool_calls = meta.get("toolCalls") or []
    for item in tool_calls:
        if not isinstance(item, dict):
            continue
        args = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
        meta_item = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        action_id = str(args.get("actionId") or meta_item.get("actionId") or "").strip()
        if action_id:
            out.append(action_id)
    return out


def _paths(meta: dict, payload: dict | None) -> list[str]:
    out: list[str] = []
    tool_calls = []
    if isinstance(payload, dict):
        tool_calls = payload.get("toolCalls") or []
    if not tool_calls and isinstance(meta, dict):
        tool_calls = meta.get("toolCalls") or []
    for item in tool_calls:
        if not isinstance(item, dict):
            continue
        meta_item = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        path = str(meta_item.get("path") or (item.get("arguments") or {}).get("path") or "").strip()
        if path:
            out.append(path)
    return out


def _unwrap(payload: Any) -> tuple[dict, dict, str]:
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
    return msg, meta, content


def _family_ok(expect: Any, paths: list[str], action_ids: list[str]) -> bool:
    families = expect if isinstance(expect, list) else [expect]
    haystack = " ".join(paths + action_ids).lower()
    mapping = {
        "stock": ("/stock", "stock"),
        "schedule": ("schedule", "program"),
        "commercial_rol": ("/rol", "rol"),
        "closing_rate": ("closing", "fechamento"),
        "capabilities": (),
        "smalltalk": (),
        "knowledge": (),
        "nebula_export": ("export", "spreadsheet", "dump"),
        "forbidden": (),
        "write": (),
        "injection": (),
    }
    for family in families:
        tokens = mapping.get(str(family), (str(family),))
        if not tokens:
            continue
        if not any(token in haystack for token in tokens):
            return False
    return True


def main() -> int:
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    required = list(fixture.get("requiredDimensions") or ["R2", "R9"])
    token = _token()
    session = _http_json(
        "POST",
        f"{_BASE}{_CHAT}/sessions",
        token=token,
        body={"agentId": _AGENT_ID, "title": f"smoke-e8-{fixture.get('id')}"},
    )
    session_id = str((session or {}).get("id") or "").strip()
    if not session_id:
        print("FAIL create session", session, flush=True)
        return 1

    evidence: dict[str, Any] = {
        "sessionId": session_id,
        "fixtureId": fixture.get("id"),
        "fixturePath": str(_FIXTURE),
        "requiredDimensions": required,
        "turns": [],
        "dimensions": {item: "INCONCLUSIVE" for item in required},
    }
    failures: list[str] = []

    for spec in fixture.get("turns") or []:
        message = str(spec.get("message") or "").replace("{SMOKE_MP_CODE}", _MP)
        print(f"--- {spec.get('id')}: {message}", flush=True)
        t0 = time.time()
        try:
            payload = _http_json(
                "POST",
                f"{_BASE}{_CHAT}/sessions/{session_id}/messages",
                token=token,
                body={
                    "message": message,
                    "agentId": _AGENT_ID,
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
        _msg, meta, content = _unwrap(payload)
        payload_dict = payload if isinstance(payload, dict) else {}
        action_ids = _action_ids(meta, payload_dict)
        paths = _paths(meta, payload_dict)
        presentation = str(
            (meta.get("presentationDecision") or {}).get("selected")
            or meta.get("requestedPresentation")
            or ""
        )
        turn = {
            "id": spec.get("id"),
            "wallMs": wall,
            "paths": paths,
            "actionIds": action_ids,
            "presentation": presentation,
            "prosePreview": content.strip()[:280],
            "plannerRoundCount": meta.get("plannerRoundCount")
            or (meta.get("boundedPlanner") or {}).get("plannerRoundCount"),
        }
        evidence["turns"].append(turn)
        print(json.dumps(turn, ensure_ascii=False, indent=2), flush=True)

        if spec.get("forbidOperationalTool") and (paths or action_ids):
            failures.append(f"{spec.get('id')}: operational tool forbidden")
        if spec.get("forbidSecretEcho") and "sk-" in content.lower():
            failures.append(f"{spec.get('id')}: secret echo")
        expect_family = spec.get("expectFamily")
        if expect_family and not spec.get("forbidOperationalTool"):
            if not _family_ok(expect_family, paths, action_ids):
                failures.append(f"{spec.get('id')}: family {expect_family} not evidenced")
        expect_presentation = spec.get("expectPresentation")
        if expect_presentation and presentation != expect_presentation:
            failures.append(
                f"{spec.get('id')}: presentation {presentation!r} != {expect_presentation!r}"
            )

    if "R2" in evidence["dimensions"]:
        evidence["dimensions"]["R2"] = "FAIL" if failures else "PASS"
    if "R9" in evidence["dimensions"]:
        evidence["dimensions"]["R9"] = "FAIL" if failures else "PASS"
    if "R3" in evidence["dimensions"]:
        iso_ok = all(
            "formato de data inválido" not in str(item.get("prosePreview") or "").lower()
            for item in evidence["turns"]
        )
        evidence["dimensions"]["R3"] = "PASS" if iso_ok and not failures else (
            "FAIL" if not iso_ok else evidence["dimensions"]["R3"]
        )
    if "R5" in evidence["dimensions"]:
        evidence["dimensions"]["R5"] = "INCONCLUSIVE"
    if "R6" in evidence["dimensions"]:
        evidence["dimensions"]["R6"] = "INCONCLUSIVE"
    if "R10" in evidence["dimensions"]:
        evidence["dimensions"]["R10"] = "FAIL" if any(
            "secret echo" in item for item in failures
        ) else "INCONCLUSIVE"

    statuses = [evidence["dimensions"][item] for item in required]
    if any(item == "FAIL" for item in statuses):
        evidence["caseStatus"] = "FAIL"
    elif any(item == "INCONCLUSIVE" for item in statuses):
        evidence["caseStatus"] = "INCONCLUSIVE"
    elif all(item == "PASS" for item in statuses):
        evidence["caseStatus"] = "PASS"
    else:
        evidence["caseStatus"] = "WARN"
    evidence["failures"] = failures

    out_path = _ROOT / _OUT if not os.path.isabs(_OUT) else Path(_OUT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"caseStatus": evidence["caseStatus"], "failures": failures}, ensure_ascii=False), flush=True)
    return 0 if evidence["caseStatus"] != "FAIL" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc}", flush=True)
        raise
