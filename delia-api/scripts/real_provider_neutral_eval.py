"""§6.130 provider-neutral orchestration live eval — run inside delpi-delia-api.

End-to-end probes through the real HTTP boundary:

  A. MCP read regression (DAVI product read)
  B. OpenAPI provider read (api-delpi declared capabilities)
  C. Workspace-context grounding (current slide via VISTA
     get_playlist_context reached from a bounded untrusted hint)
  D. Governed write PREPARE -> REJECT through VISTA
  E. Fail-closed workspace payload (malformed -> invalid_request;
     oversized refs rejected)

Required env (never printed): DEV_PORTAL_USERNAME, DEV_PORTAL_PASSWORD.
Optional: DELIA_EVAL_PLAYLIST_ID, DELIA_EVAL_SLIDE_ID.

Never prints tokens, secrets, or authorization headers.
Exit code 0 always — results are in the report.
"""

from __future__ import annotations

import base64
import json
import os

import requests

BASE = "http://localhost:8000"
PLAYLIST_ID = (
    os.getenv("DELIA_EVAL_PLAYLIST_ID")
    or "16746517-51a1-4011-af8c-047fb12c2524"
)
SLIDE_ID = (
    os.getenv("DELIA_EVAL_SLIDE_ID")
    or "d7c2b467-10f7-471a-b134-c44af4f3aa6f"
)


def _claims(jwt: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(jwt.split(".")[1] + "=="))


def _mint_subject_token() -> tuple[str, dict]:
    url = (
        f"{os.environ['KEYCLOAK_URL']}/realms/{os.environ['KEYCLOAK_REALM']}"
        "/protocol/openid-connect/token"
    )
    response = requests.post(
        url,
        headers={"Host": os.environ.get("DELIA_EXCHANGE_HOST_HEADER") or
                 "minhadelpi.com.br"},
        data={
            "grant_type": "password",
            "client_id": os.getenv("DEV_KC_CLIENT_ID") or "delpi-central",
            "username": os.environ["DEV_PORTAL_USERNAME"],
            "password": os.environ["DEV_PORTAL_PASSWORD"],
            "scope": "openid",
        },
        timeout=10,
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    claims = _claims(token)
    return token, {
        "sub_present": bool(claims.get("sub")),
        "azp": claims.get("azp"),
        "exp_in_seconds": int(claims.get("exp") or 0)
        - int(__import__("time").time()),
    }


def _turn(token: str, text: str, workspace: dict | None = None) -> dict:
    body: dict = {"input": text}
    if workspace is not None:
        body["workspace"] = workspace
    response = requests.post(
        f"{BASE}/interaction/turns",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=90,
    )
    payload = response.json()
    provenance = payload.get("provenance") or {}
    return {
        "http_status": response.status_code,
        "code": payload.get("code"),
        "grounding_status": payload.get("grounding_status"),
        "epistemic_class": payload.get("epistemic_class"),
        "provider_id": provenance.get("provider_id"),
        "group_id": provenance.get("capability_group_id"),
        "remote_capability": provenance.get("remote_capability"),
        "has_confirmation": bool(payload.get("confirmation_request")),
        "confirmation": payload.get("confirmation_request"),
        "session_id": payload.get("session_id"),
        "limitations": payload.get("limitations"),
        "content_prefix": str(payload.get("content") or "")[:160],
    }


def _confirm(token: str, confirmation: dict, decision: str) -> dict:
    return _turn_turn_body(
        token,
        {
            "input": "decisão do usuário",
            "confirmation": {
                "decision": decision,
                "proposal_digest": confirmation["proposal_digest"],
                "preview_fingerprint": confirmation["preview_fingerprint"],
                "session_id": confirmation["session_id"],
            },
        },
    )


def _turn_turn_body(token: str, body: dict) -> dict:
    response = requests.post(
        f"{BASE}/interaction/turns",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=90,
    )
    payload = response.json()
    provenance = payload.get("provenance") or {}
    return {
        "http_status": response.status_code,
        "code": payload.get("code"),
        "grounding_status": payload.get("grounding_status"),
        "provider_id": provenance.get("provider_id"),
        "remote_capability": provenance.get("remote_capability"),
        "content_prefix": str(payload.get("content") or "")[:160],
    }


def _workspace() -> dict:
    return {
        "host_app_id": "tv-dashboard",
        "view_ref": "deck_editor",
        "selected_entity_ref": {
            "entity_type": "slide",
            "entity_id": SLIDE_ID,
            "source_system": "vista",
        },
        "entity_refs": [
            {
                "entity_type": "slide",
                "entity_id": SLIDE_ID,
                "source_system": "vista",
            },
            {
                "entity_type": "playlist",
                "entity_id": PLAYLIST_ID,
                "source_system": "vista",
            },
        ],
    }


def main() -> int:
    token, claims = _mint_subject_token()
    report: dict = {"subject_token": claims}

    # A. MCP read regression — product search stays grounded.
    report["mcp_product_read"] = _turn(
        token, "busque o produto pelo código 40.001"
    )

    # B. OpenAPI provider — api-delpi declared READ capability.
    report["openapi_product_search"] = _turn(
        token, "liste produtos delpi com termo 'rosca'"
    )

    # C. Workspace context — "slide atual" resolved via VISTA.
    report["workspace_current_slide"] = _turn(
        token,
        "descreva o slide que estou editando agora",
        workspace=_workspace(),
    )

    # D. Governed write PREPARE -> REJECT (VISTA prepare_change).
    prepare = _turn(
        token,
        "renomeie a playlist que estou vendo para 'teste avaliação'",
        workspace=_workspace(),
    )
    report["write_prepare"] = prepare
    confirmation = prepare.get("confirmation") or {}
    if confirmation:
        report["write_reject"] = _confirm(token, confirmation, "REJECT")

    # E. Fail-closed: malformed workspace payloads.
    report["malformed_workspace_missing_host"] = _turn(
        token, "olá", workspace={"view_ref": "x"}
    )
    report["malformed_workspace_oversized"] = _turn(
        token,
        "olá",
        workspace={"host_app_id": "x" * 300},
    )

    report["unauthenticated"] = requests.post(
        f"{BASE}/interaction/turns",
        json={"input": "produtos"},
        timeout=10,
    ).status_code

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
