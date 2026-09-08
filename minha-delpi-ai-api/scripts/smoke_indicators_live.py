#!/usr/bin/env python3
"""Live smoke — Wave I indicators (I1–I6) with L1–L4 light gates.

Fixtures: SMOKE_BRANCH, SMOKE_PERIOD (no product). Protocol §16.1 +
docs/testing/smoke-complex-consolidated-turns.md Wave I.
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
_BRANCH = os.environ.get("SMOKE_BRANCH", "01").strip() or "01"
_PERIOD = os.environ.get("SMOKE_PERIOD", "agosto 2026").strip() or "agosto 2026"
_AGENT_ID = os.environ.get(
    "SMOKE_AGENT_ID", "4f9c225b-0414-40d3-a462-040889719b83"
).strip()
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/testing/evidence/chat-indicators-live.json",
).strip()
_PAUSE = float(os.environ.get("SMOKE_CASE_PAUSE", "3"))

_DEPT_MARKERS = (
    "/department-indicators",
    "/departments-indicators",
    "/department-idd",
)


def _cases() -> list[dict[str, Any]]:
    rol_filial = (
        f"Qual o ROL da filial {_BRANCH} em {_PERIOD}? "
        f"Quero o consolidado financeiro da filial."
    )
    return [
        {
            "id": "I1-financial-rol",
            "message": rol_filial,
            "require_any_path": ["/financial/rol"],
            "forbid_only_path": ["/commercial/rol/by-branch"],
            "forbid_any_path": list(_DEPT_MARKERS),
            "expect_prose_min": 40,
            "negative": False,
        },
        {
            "id": "I2-commercial-rol-series",
            "message": (
                f"Quero o ROL / indicadores comerciais de {_PERIOD}: mostre o "
                f"número principal (KPI), a série no tempo em gráfico se "
                f"disponível, e uma leitura em prosa."
            ),
            "require_any_path": [
                "/commercial/rol/series",
                "/commercial/rol/summary",
                "/financial/rol",
                "/commercial/rol",
            ],
            "forbid_any_path": list(_DEPT_MARKERS) + ["/stock"],
            "expect_prose_min": 40,
            "negative": False,
        },
        {
            "id": "I3-neg-by-branch-only",
            "message": rol_filial,
            "require_any_path": ["/financial/rol"],
            "forbid_only_path": ["/commercial/rol/by-branch"],
            "forbid_any_path": list(_DEPT_MARKERS),
            "expect_prose_min": 20,
            "negative": True,
            "note": "Mesmo texto I1 — falha L1 se o único path for by-branch",
        },
        {
            "id": "I4-closing-rate",
            "message": (
                f"Qual a taxa de fechamento / conversão de vendas da filial "
                f"{_BRANCH} em {_PERIOD}?"
            ),
            "require_any_path": ["/commercial/closing-rate"],
            "forbid_any_path": list(_DEPT_MARKERS),
            "expect_prose_min": 30,
            "negative": False,
        },
        {
            "id": "I5-sales-order-otd",
            "message": (
                f"Qual o OTD de pedidos de venda da filial {_BRANCH} em {_PERIOD}?"
            ),
            "require_any_path": ["/commercial/sales-order-otd", "/sales-order-otd"],
            "forbid_any_path": list(_DEPT_MARKERS),
            "expect_prose_min": 30,
            "negative": False,
        },
        {
            "id": "I6-neg-department-indicators",
            "message": (
                f"Mostre o ROL comercial recente ({_PERIOD}) com KPI e leitura "
                f"em prosa — indicadores comerciais, não painel de departamento."
            ),
            "require_any_path": [
                "/commercial/rol",
                "/financial/rol",
                "/commercial/",
            ],
            "forbid_any_path": list(_DEPT_MARKERS),
            "expect_prose_min": 30,
            "negative": True,
        },
    ]


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


def _paths_from_payload(payload: dict) -> list[str]:
    out: list[str] = []
    msg = payload
    if isinstance(payload.get("message"), dict):
        msg = payload["message"]
    tool_calls = msg.get("toolCalls") or payload.get("toolCalls") or []
    meta = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
    if not tool_calls and isinstance(meta.get("toolCalls"), list):
        tool_calls = meta["toolCalls"]
    for tc in tool_calls:
        if not isinstance(tc, dict):
            continue
        m = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        path = str(m.get("path") or "").strip()
        if path:
            out.append(path)
    return out


def _content(payload: dict) -> str:
    msg = payload
    if isinstance(payload.get("message"), dict):
        msg = payload["message"]
    for source in (msg, payload):
        for key in ("content", "answer", "text"):
            if str(source.get(key) or "").strip():
                return str(source.get(key))
    return ""


def _eval_case(case: dict[str, Any], paths: list[str], content: str) -> list[str]:
    failures: list[str] = []
    joined = " ".join(paths).lower()
    require = case.get("require_any_path") or []
    if require and not any(str(m).lower() in joined for m in require):
        failures.append(f"L1: nenhum path canônico {require}; got={paths}")

    forbid_only = case.get("forbid_only_path") or []
    if forbid_only and paths:
        # Fail if every path matches forbid_only and none is financial/rol.
        only_forbidden = all(
            any(str(m).lower() in p.lower() for m in forbid_only) for p in paths
        )
        has_financial = any("/financial/rol" in p.lower() for p in paths)
        if only_forbidden and not has_financial:
            failures.append(
                f"L1: único path é by-branch (proibido para ROL filial): {paths}"
            )

    forbid_any = case.get("forbid_any_path") or []
    if forbid_any and paths:
        hits = [
            p
            for p in paths
            if any(str(m).lower() in p.lower() for m in forbid_any)
        ]
        if any(any(m in p.lower() for m in _DEPT_MARKERS) for p in hits):
            failures.append(f"L1: department/IDD path presente: {hits}")
        elif any("/stock" in p.lower() for p in hits) and not any(
            x in joined for x in ("/rol", "/commercial", "/financial", "/kpi")
        ):
            failures.append(f"L1: paths só estoque sem indicador: {hits}")

    min_chars = int(case.get("expect_prose_min") or 0)
    if min_chars and len(content.strip()) < min_chars:
        failures.append(f"L2/L4: prosa curta ({len(content.strip())} < {min_chars})")

    return failures


def main() -> int:
    print(
        f"base={_BASE} branch={_BRANCH} period={_PERIOD!r} agent={_AGENT_ID}",
        flush=True,
    )
    token = _token()
    cases = _cases()
    results: list[dict[str, Any]] = []
    fail_count = 0

    for index, case in enumerate(cases):
        if index:
            time.sleep(_PAUSE)
        token = _token()
        print("=" * 72, flush=True)
        print(f"CASE {case['id']}", flush=True)
        print(f"MSG  {case['message'][:140]}…", flush=True)
        try:
            session = _http_json(
                "POST",
                f"{_BASE}{_CHAT}/sessions",
                token=token,
                body={"agentId": _AGENT_ID, "title": f"smoke-{case['id']}"[:80]},
            )
            session_id = str((session or {}).get("id") or "").strip()
            t0 = time.time()
            payload = _http_json(
                "POST",
                f"{_BASE}{_CHAT}/sessions/{session_id}/messages",
                token=token,
                body={
                    "message": case["message"],
                    "agentId": _AGENT_ID,
                    "responseMode": _MODE,
                    "includeAdminDebug": True,
                    "adminDebug": True,
                },
            )
            wall = int((time.time() - t0) * 1000)
            paths = _paths_from_payload(payload if isinstance(payload, dict) else {})
            content = _content(payload if isinstance(payload, dict) else {})
            errors = _eval_case(case, paths, content)
            row = {
                "id": case["id"],
                "sessionId": session_id,
                "routeFamily": "indicator",
                "productKind": "none",
                "wallMs": wall,
                "paths": paths,
                "proseChars": len(content.strip()),
                "prosePreview": content.strip()[:280],
                "errors": errors,
                "passed": not errors,
                "negative": bool(case.get("negative")),
            }
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:400]
            row = {
                "id": case["id"],
                "passed": False,
                "errors": [f"HTTP {exc.code}: {body}"],
                "paths": [],
            }
        except Exception as exc:  # noqa: BLE001
            row = {
                "id": case["id"],
                "passed": False,
                "errors": [f"{type(exc).__name__}: {exc}"],
                "paths": [],
            }

        results.append(row)
        status = "PASS" if row["passed"] else "FAIL"
        print(f"{status} paths={row.get('paths')}", flush=True)
        for err in row.get("errors") or []:
            print(f"  - {err}", flush=True)
        if not row["passed"]:
            fail_count += 1

    evidence = {
        "baseUrl": _BASE,
        "branch": _BRANCH,
        "period": _PERIOD,
        "agentId": _AGENT_ID,
        "routeFamily": "indicator",
        "harnessLayer": "l1-l4-light",
        "passed": fail_count == 0,
        "failCount": fail_count,
        "caseCount": len(results),
        "releaseNote": (
            "Wave I indicators. Release still requires full L1–L4 review per §16.1."
        ),
        "results": results,
    }
    out_path = _OUT if os.path.isabs(_OUT) else os.path.join(os.getcwd(), _OUT)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, ensure_ascii=False, indent=2)
    print("=" * 72, flush=True)
    print(f"evidence={out_path}", flush=True)
    print(
        f"SUMMARY {'PASS' if fail_count == 0 else 'FAIL'} "
        f"({len(results) - fail_count}/{len(results)})",
        flush=True,
    )
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
