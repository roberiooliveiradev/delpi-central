"""Read-only governed path probe for systemic intelligence audit.

Never prints secrets. Writes sanitized JSON to stdout.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


def _runtime_model_identity() -> tuple[str, str]:
    """(provider, model_name) from the unified runtime JSON — probes
    report the resolved snapshot, never a retired env var."""
    import pathlib
    data = json.loads(
        (
            pathlib.Path(__file__).resolve().parents[1]
            / "config"
            / "pydantic_ai.runtime.delpi.json"
        ).read_text(encoding="utf-8")
    )
    profile = data["profiles"][
        os.getenv("DELIA_RUNTIME_PROFILE") or data["default_profile"]
    ]
    return (
        profile["model"]["provider"],
        profile["model"]["model_name"],
    )



CASES = (
    ("e01_sipoc", "O que é SIPOC?"),
    ("e06_unavailable", "Consulte a estrutura do produto ZZZ99999inexistente."),
)


def _mint() -> str:
    url = os.getenv("DELIA_E2E_TOKEN_URL") or (
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
        url,
        data=data,
        method="POST",
        headers={"Host": os.getenv("DELIA_E2E_TOKEN_HOST") or "localhost"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())["access_token"]


def _turn(token: str, text: str, *, timeout: float = 90.0) -> dict:
    base = os.getenv("DELIA_API_BASE") or "http://127.0.0.1:8000"
    body = json.dumps({"input": text}).encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/interaction/turns",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            status = resp.status
    except TimeoutError:
        return {
            "error": "TimeoutError",
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() if exc.fp else ""
        status = exc.code
    except Exception as exc:  # noqa: BLE001
        return {
            "error": type(exc).__name__,
            "error_msg": str(exc)[:160],
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {
            "http_status": status,
            "elapsed_ms": elapsed_ms,
            "parse_error": True,
            "raw_prefix": raw[:160],
        }
    return {
        "http_status": status,
        "elapsed_ms": elapsed_ms,
        "grounding_status": payload.get("grounding_status"),
        "epistemic_class": payload.get("epistemic_class"),
        "code": payload.get("code"),
        "limitations": list(payload.get("limitations") or [])[:20],
        "content_prefix": str(payload.get("content") or "")[:200],
    }


def main() -> int:
    report: dict = {
        "runtime_sha_env": os.getenv("DELIA_RUNTIME_SHA"),
        "model": _runtime_model_identity()[1],
    }
    try:
        token = _mint()
        report["mint_ok"] = True
    except Exception as exc:  # noqa: BLE001
        report["mint_error"] = type(exc).__name__
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2
    for key, text in CASES:
        report[key] = _turn(token, text)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
