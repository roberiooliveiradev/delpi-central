"""Bounded live E2E probe for E4-R6 RC-A remediation (homologation).

Never prints tokens/secrets. Writes a sanitized JSON report to stdout.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


COMPARE_TEXT = (
    "Compare as estruturas de produto 90260147 e 90260148: "
    "itens comuns, exclusivos de cada uma e diferenças relevantes."
)
THIRD_SPEC_TEXT = (
    "Compare as estruturas 90260147 e 90260148 usando a última "
    "especificação de engenharia aprovada como terceira fonte."
)


def _claims(jwt: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(jwt.split(".")[1] + "=="))


def _mint() -> tuple[str, dict]:
    # Prefer the public gateway path so token ``iss`` matches
    # ``KEYCLOAK_ISSUER`` (http://localhost/auth/realms/delpi). Direct
    # keycloak:8080 mints iss with :8080 and fails JWT validation.
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
    host_header = os.getenv("DELIA_E2E_TOKEN_HOST") or "localhost"
    req = urllib.request.Request(
        token_url,
        data=data,
        method="POST",
        headers={"Host": host_header},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode())
    token = body["access_token"]
    claims = _claims(token)
    aud = claims.get("aud")
    sanitized = {
        "sub_present": bool(claims.get("sub")),
        "azp": claims.get("azp"),
        "iss": claims.get("iss"),
        "has_delia_aud": (
            ("delia-api" in aud)
            if isinstance(aud, list)
            else aud == "delia-api"
        ),
        "exp_in_seconds": int(claims.get("exp") or 0) - int(time.time()),
    }
    return token, sanitized


def _post_turn(
    token: str,
    text: str,
    *,
    accept: str = "application/json",
    timeout: float = 120.0,
) -> dict:
    base = os.getenv("DELIA_API_BASE") or "http://127.0.0.1:8000"
    body = json.dumps({"input": text}).encode()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": accept,
    }
    host = os.getenv("DELIA_E2E_API_HOST")
    if host:
        headers["Host"] = host
    req = urllib.request.Request(
        f"{base.rstrip('/')}/interaction/turns",
        data=body,
        method="POST",
        headers=headers,
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
    except TimeoutError as exc:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return {
            "http_status": None,
            "content_type": None,
            "elapsed_ms": elapsed_ms,
            "error": "TimeoutError",
            "error_msg": str(exc)[:120],
        }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() if exc.fp else ""
        status = exc.code
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
    except Exception as exc:  # noqa: BLE001 — capture blocker
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return {
            "http_status": None,
            "content_type": None,
            "elapsed_ms": elapsed_ms,
            "error": type(exc).__name__,
            "error_msg": str(exc)[:200],
        }
    elapsed_ms = int((time.monotonic() - started) * 1000)

    if "ndjson" in accept:
        events = []
        terminal = None
        terminal_meta = None
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                events.append({"parse_error": True, "prefix": line[:80]})
                continue
            etype = evt.get("type") or evt.get("event")
            events.append(
                {
                    "type": etype,
                    "keys": sorted(evt.keys())[:20],
                }
            )
            if etype in {"turn_result", "turn_error"} or "grounding_status" in evt:
                # Payload may be nested under result/turn_result/data.
                nested = (
                    evt.get("result")
                    or evt.get("turn_result")
                    or evt.get("data")
                    or evt
                )
                terminal = nested if isinstance(nested, dict) else evt
                terminal_meta = evt
        report = {
            "http_status": status,
            "content_type": content_type,
            "elapsed_ms": elapsed_ms,
            "event_count": len(events),
            "event_types": [e.get("type") for e in events],
            "terminal_present": terminal is not None,
            "terminal_event_keys": (
                sorted(terminal_meta.keys())[:30]
                if terminal is not None
                else None
            ),
        }
        if terminal:
            report.update(_sanitize_turn(terminal))
        return report

    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {
            "http_status": status,
            "content_type": content_type,
            "elapsed_ms": elapsed_ms,
            "parse_error": True,
            "raw_prefix": raw[:200],
        }
    out = {
        "http_status": status,
        "content_type": content_type,
        "elapsed_ms": elapsed_ms,
    }
    out.update(_sanitize_turn(payload))
    return out


def _sanitize_turn(body: dict) -> dict:
    provenance = body.get("provenance") or {}
    composition = None
    if isinstance(provenance, dict):
        composition = provenance.get("composition")
    verified = body.get("verified_composition")
    limitations = body.get("limitations") or ()
    if isinstance(limitations, list):
        limitations = tuple(limitations)
    content = str(body.get("content") or "")
    return {
        "code": body.get("code"),
        "grounding_status": body.get("grounding_status"),
        "epistemic_class": body.get("epistemic_class"),
        "task_outcome": body.get("task_outcome"),
        "limitations": list(limitations)[:30],
        "comparison_limitations": [
            lim
            for lim in limitations
            if isinstance(lim, str) and lim.startswith("comparison_")
        ],
        "has_verified_composition_field": verified is not None,
        "provenance_source_present": bool(
            isinstance(provenance, dict) and provenance.get("source")
        ),
        "composition_keys": (
            sorted(composition.keys())[:20]
            if isinstance(composition, dict)
            else None
        ),
        "composition_roots": (
            composition.get("source_roots")
            if isinstance(composition, dict)
            else None
        ),
        "composition_verdict": (
            composition.get("verdict")
            if isinstance(composition, dict)
            else None
        ),
        "content_prefix": content[:240],
        "mentions_50220013": "50220013" in content,
        "mentions_50220014": "50220014" in content,
        "mentions_10030015": "10030015" in content,
        "mentions_10030019": "10030019" in content,
        "mentions_10080031": "10080031" in content,
    }


def main() -> int:
    report: dict = {
        "runtime_sha_env": os.getenv("DELIA_RUNTIME_SHA"),
        "model": os.getenv("DELIA_LLM_MODEL"),
        "provider": os.getenv("DELIA_LLM_PROVIDER"),
    }
    try:
        token, claims = _mint()
        report["subject_token"] = claims
    except Exception as exc:  # noqa: BLE001 — report blocker
        report["mint_error"] = type(exc).__name__
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    # Remint before each long turn — password-grant tokens expire ~300s
    # and a single compare can consume most of that window.
    def _fresh() -> str:
        fresh, claims = _mint()
        report.setdefault("subject_token_refreshes", []).append(claims)
        return fresh

    report["compare_ndjson"] = _post_turn(
        _fresh(),
        COMPARE_TEXT,
        accept="application/x-ndjson",
        timeout=300.0,
    )
    report["compare_json"] = _post_turn(
        _fresh(), COMPARE_TEXT, timeout=300.0
    )
    report["third_spec_json"] = _post_turn(
        _fresh(), THIRD_SPEC_TEXT, timeout=300.0
    )

    false_grounded = 0
    for key in ("compare_json", "compare_ndjson", "third_spec_json"):
        g = (report.get(key) or {}).get("grounding_status")
        # False GROUNDED: success composition claimed without roots /
        # or third-spec path grounding without third source.
        if g == "GROUNDED" and key == "third_spec_json":
            # If it grounded a three-source ask without composition roots
            # including a third identity, count as false.
            roots = (report[key].get("composition_roots") or []) or []
            if len(roots) < 3:
                false_grounded += 1
        if g == "GROUNDED" and key.startswith("compare"):
            # Valid only if two roots present; otherwise suspicious.
            roots = (report[key].get("composition_roots") or []) or []
            if len(roots) != 2:
                false_grounded += 1
    report["false_grounded_heuristic_count"] = false_grounded
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
