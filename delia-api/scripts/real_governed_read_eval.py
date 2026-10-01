"""C4-MCP-GOVERNED-READS-01 live eval — run inside delpi-delia-api.

End-to-end proof through the real HTTP boundary:

  Portal dev user (password grant, scope=openid)
    -> POST /interaction/turns (real auth middleware -> Core /me)
    -> governed read attempt -> DAVI discover_delpi_information
    -> search_products candidate -> execute_delpi_information
    -> grounded InteractiveTurnResult

Also runs a non-product control question (expected NON_GROUNDED).

Required env (never printed): DEV_PORTAL_USERNAME, DEV_PORTAL_PASSWORD.
Optional: DELIA_EVAL_PRODUCT_QUERY (default a generic product query).

Never prints tokens, secrets, or authorization headers.
Exit code 0 always — results are in the report.
"""

from __future__ import annotations

import base64
import json
import os

import requests


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
    sanitized = {
        "sub_present": bool(claims.get("sub")),
        "azp": claims.get("azp"),
        "has_requester_audience": "delia-api" in (
            claims.get("aud") if isinstance(claims.get("aud"), list)
            else [claims.get("aud")]
        ),
        "mcp_resource_audiences": [
            a for a in (claims.get("aud") or [])
            if isinstance(a, str) and a.endswith("/mcp")
        ] if isinstance(claims.get("aud"), list) else [],
        "scope": sorted(str(claims.get("scope") or "").split()),
        "exp_in_seconds": int(claims.get("exp") or 0)
        - int(__import__("time").time()),
    }
    return token, sanitized


def _turn(token: str, text: str) -> dict:
    response = requests.post(
        "http://localhost:8000/interaction/turns",
        json={"input": text},
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    body = response.json()
    report = {
        "http_status": response.status_code,
        "code": body.get("code"),
        "grounding_status": body.get("grounding_status"),
        "epistemic_class": body.get("epistemic_class"),
        "limitations": body.get("limitations"),
        "provenance": body.get("provenance"),
        "item_lines": sum(
            1 for line in str(body.get("content") or "").splitlines()
            if line.startswith("- ")
        ),
        "content_prefix": str(body.get("content") or "")[:160],
    }
    return report


def main() -> int:
    token, claims = _mint_subject_token()
    query = os.getenv("DELIA_EVAL_PRODUCT_QUERY") or (
        "quero encontrar um produto pelo código"
    )
    report = {
        "subject_token": claims,
        "product_query": _turn(token, query),
        "control_query": _turn(token, "o que você pode fazer?"),
        "unauthenticated": requests.post(
            "http://localhost:8000/interaction/turns",
            json={"input": "produtos"},
            timeout=10,
        ).status_code,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
