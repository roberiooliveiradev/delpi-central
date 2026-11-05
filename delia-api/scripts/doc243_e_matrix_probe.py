"""Doc 243 — E01..E10 live matrix on the rebuilt single-runtime DÉLIA.

Runs inside delpi-delia-api (dev network). Mints a real dev user token
through the gateway, POSTs real turns, prints a sanitized JSON report —
never tokens, secrets or raw prompts.

Required env (never printed): DEV_PORTAL_USERNAME, DEV_PORTAL_PASSWORD.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


def _claims(jwt: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(jwt.split(".")[1] + "=="))


def _mint() -> str:
    token_url = os.getenv("DELIA_E2E_TOKEN_URL") or (
        "http://gateway/auth/realms/"
        f"{os.environ.get('KEYCLOAK_REALM', 'delpi')}"
        "/protocol/openid-connect/token"
    )
    data = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": os.getenv("DEV_KC_CLIENT_ID") or "delpi-central",
            "username": os.environ["DEV_PORTAL_USERNAME"],
            "password": os.environ["DEV_PORTAL_PASSWORD"],
            "scope": "openid",
        }
    ).encode()
    req = urllib.request.Request(
        token_url, data=data, method="POST",
        headers={"Host": os.getenv("DELIA_E2E_TOKEN_HOST") or "localhost"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())["access_token"]


def _turn(token, text, *, accept="application/json", timeout=180.0, prior=None):
    base = os.getenv("DELIA_API_BASE") or "http://127.0.0.1:8000"
    payload = {"input": text}
    if prior:
        payload["context"] = prior
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/interaction/turns",
        data=body, method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": accept,
        },
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() if exc.fp else ""
        status = exc.code
    except Exception as exc:  # noqa: BLE001
        return {
            "http_status": None,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "error": type(exc).__name__,
        }
    elapsed_ms = int((time.monotonic() - started) * 1000)
    out = {"http_status": status, "elapsed_ms": elapsed_ms}
    if "ndjson" in accept:
        lines = [l for l in raw.splitlines() if l.strip()]
        out["ndjson_lines"] = len(lines)
        out["terminal_kind"] = (
            json.loads(lines[-1]).get("kind")
            if lines else None
        )
        try:
            result = json.loads(lines[-1]).get("result") or {}
        except Exception:
            result = {}
        out["grounding"] = (result.get("grounding_status")
                            or result.get("grounding"))
    else:
        try:
            body = json.loads(raw)
        except Exception:
            body = {}
        out["grounding"] = body.get("grounding_status") or body.get(
            "grounding"
        )
        out["status"] = body.get("status")
        out["error_code"] = body.get("error_code")
        out["content_head"] = str(body.get("content") or "")[:160]
        out["usage"] = (body.get("observability") or {}).get("llm_usage")
        out["collected"] = (
            body.get("observability") or {}
        ).get("capability_attempts")
    return out


CASES = [
    ("E01", "O que é SIPOC?", "json"),
    ("E02", "Qual a estrutura do produto 90260147?", "json"),
    ("E03", "Compare as estruturas de produto 90260147 e 90260148: "
            "itens comuns, exclusivos de cada uma e diferenças relevantes.",
     "json"),
    ("E04", "Mostre a estrutura do produto 90260147 e o que diz o guia "
            "de produção relacionado.", "json"),
    ("E05", "Busque o produto 90260148 e mostre sua estrutura.", "json"),
    ("E06", "Explique o conceito de estrutura de produto e mostre a "
            "estrutura do produto 90260147.", "json"),
    ("E07a", "Qual a estrutura?", "json"),
    ("E07b", "90260147", "json_prior"),
    ("E08", "Exclua o produto 90260147.", "json"),
    ("E09", "Qual a estrutura do produto 90260147?", "ndjson"),
    ("E10", "Mostre a estrutura dos produtos 90260147, 90260148 e "
            "50220013.", "json"),
]


def main() -> int:
    token = _mint()
    report = {"cases": {}, "sha": os.getenv("DELIA_RUNTIME_SHA")}
    prior = None
    for case_id, text, mode in CASES:
        accept = (
            "application/x-ndjson" if mode == "ndjson"
            else "application/json"
        )
        kwargs = {}
        if mode == "json_prior":
            kwargs["prior"] = prior
        result = _turn(token, text, accept=accept, **kwargs)
        report["cases"][case_id] = result
        print(f"== {case_id} {result.get('http_status')} "
              f"{result.get('grounding')} {result.get('elapsed_ms')}ms")
        if case_id == "E07a":
            prior = [
                {"kind": "USER_INPUT", "content": text},
                {"kind": "DELIA_RESULT",
                 "content": result.get("content_head") or "clarify"},
            ]
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
