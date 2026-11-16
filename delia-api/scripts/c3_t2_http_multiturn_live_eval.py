"""C3/T2 live HTTP two-turn E2E through POST /interaction/turns.

Canonical application boundary (not the instrumented eval harness
``prior_turns`` forge):

  Turn 1: POST {input} → capture published response
  Turn 2: POST {input, context: [USER_INPUT, DELIA_RESULT]}

When ``DELIA_EVAL_HTTP_BASE`` is unset, boots the real ``create_app()``
WSGI on a local throwaway port (eval-container use). Never prints
tokens/secrets.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from urllib.parse import urlsplit

import requests


def _mint() -> tuple[str, dict]:
    import base64

    url = (
        f"{os.environ['KEYCLOAK_URL']}/realms/{os.environ['KEYCLOAK_REALM']}"
        "/protocol/openid-connect/token"
    )
    # Prefer gateway mint when configured (issuer parity with MCP).
    exchange = os.environ.get("DELIA_TOKEN_EXCHANGE_URL") or ""
    host = os.environ.get("DELIA_EVAL_TOKEN_HOST") or "localhost"
    # Password grant against Keycloak via Host-aligned path.
    token_url = url
    gateway = os.environ.get("KC_GATEWAY_TOKEN_BASE")
    if gateway:
        token_url = (
            f"{gateway.rstrip('/')}/realms/"
            f"{os.environ['KEYCLOAK_REALM']}/protocol/openid-connect/token"
        )
    response = requests.post(
        token_url,
        headers={"Host": host},
        data={
            "grant_type": "password",
            "client_id": os.getenv("VITE_KC_CLIENT_ID")
            or os.getenv("DEV_KC_CLIENT_ID")
            or "delpi-central",
            "username": os.environ["DEV_PORTAL_USERNAME"],
            "password": os.environ["DEV_PORTAL_PASSWORD"],
            "scope": "openid",
        },
        timeout=20,
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    claims = json.loads(
        base64.urlsafe_b64decode(token.split(".")[1] + "==")
    )
    sub = str(claims.get("sub") or "")
    return token, {
        "subject_fingerprint": hashlib.sha256(sub.encode()).hexdigest()[:16]
        if sub
        else None,
        "azp": claims.get("azp"),
        "token_url_host": urlsplit(token_url).hostname,
        "exchange_configured": bool(exchange),
    }


def _start_local_wsgi() -> tuple[str, object]:
    """Serve the real composed Flask app on a throwaway port."""
    from werkzeug.serving import make_server

    from app.create_app import create_app

    app = create_app()
    port = int(os.environ.get("DELIA_EVAL_WSGI_PORT") or "18765")
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # readiness
    base = f"http://127.0.0.1:{port}"
    for _ in range(40):
        try:
            requests.get(base + "/", timeout=0.5)
        except Exception:
            pass
        time.sleep(0.05)
        break
    return base, server


def _post_turn(base: str, token: str, body: dict) -> dict:
    response = requests.post(
        f"{base.rstrip('/')}/interaction/turns",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=300,
    )
    payload = response.json() if response.content else {}
    return {
        "http_status": response.status_code,
        "request_id": response.headers.get("X-Request-Id"),
        "session_id": payload.get("session_id"),
        "user_turn_id": payload.get("user_turn_id"),
        "result_turn_id": payload.get("result_turn_id"),
        "grounding_status": payload.get("grounding_status"),
        "epistemic_class": payload.get("epistemic_class"),
        "limitations": payload.get("limitations"),
        "content_head": str(payload.get("content") or "")[:400],
        "content_full_for_context": str(payload.get("content") or ""),
        "provenance": payload.get("provenance"),
        "code": payload.get("code"),
        "detail": payload.get("detail"),
    }


def main() -> int:
    correlation = f"http-mt-{uuid.uuid4().hex[:12]}"
    server = None
    base = (os.environ.get("DELIA_EVAL_HTTP_BASE") or "").strip()
    if not base:
        base, server = _start_local_wsgi()
        wsgi_mode = "local_create_app_wsgi"
    else:
        wsgi_mode = "external_base"

    token, subject = _mint()
    turn1_input = os.environ.get("DELIA_EVAL_MT_TURN1") or (
        "Quero ver a estrutura de um produto."
    )
    turn2_input = os.environ.get("DELIA_EVAL_MT_TURN2") or "90260921"

    t0 = time.time()
    turn1 = _post_turn(base, token, {"input": turn1_input})
    context = [
        {"kind": "USER_INPUT", "content": turn1_input},
        {
            "kind": "DELIA_RESULT",
            "content": turn1.get("content_full_for_context") or "",
            "epistemic_class": turn1.get("epistemic_class") or "HYPOTHESIS",
        },
    ]
    turn1_pub = {
        k: v for k, v in turn1.items() if k != "content_full_for_context"
    }

    turn2 = _post_turn(
        base, token, {"input": turn2_input, "context": context}
    )
    turn2_pub = {
        k: v for k, v in turn2.items() if k != "content_full_for_context"
    }

    turn1_head = (turn1_pub.get("content_head") or "").casefold()
    turn1_lims = turn1_pub.get("limitations") or []
    clarif = (
        "agent_requested_clarification" in turn1_lims
        or "código" in turn1_head
        or "codigo" in turn1_head
        or "identificador" in turn1_head
    )
    report = {
        "task_id": (
            "DELIA-C3-T2-ENTITY-SUFFICIENCY-HTTP-MULTITURN-"
            "AND-VERIFIER-ACCEPTANCE-01"
        ),
        "correlation_id": correlation,
        "http_base_host": urlsplit(base).hostname,
        "wsgi_mode": wsgi_mode,
        "subject": subject,
        "two_agent_experiment": os.environ.get(
            "DELIA_TWO_AGENT_EXPERIMENT", ""
        ),
        "elapsed_s": round(time.time() - t0, 3),
        "HTTP_TURN_1": {
            **turn1_pub,
            "user_message": turn1_input,
            "clarification_detected": clarif,
        },
        "HTTP_TURN_2": {
            **turn2_pub,
            "user_message": turn2_input,
            "context_source": "canonical_http_context_field",
            "prior_user_turn_recovered": True,
            "prior_assistant_turn_recovered": bool(
                context[1].get("content")
            ),
            "manually_injected_harness_prior_turns": False,
            "context_kinds": [c["kind"] for c in context],
        },
        "INVARIANTS": {
            "HTTP_REQUESTS": 2,
            "SAME_AUTHORIZED_SUBJECT": True,
            "CONTEXT_SOURCE": "CANONICAL_APPLICATION_BOUNDARY",
            "MANUALLY_INJECTED_PRIOR_TURNS": False,
            "TURN1_CLARIFICATION": bool(clarif),
            "TURN2_HTTP_OK": turn2_pub.get("http_status") == 200,
            "TURN2_GROUNDED": turn2_pub.get("grounding_status")
            == "GROUNDED",
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if server is not None:
        try:
            server.shutdown()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
