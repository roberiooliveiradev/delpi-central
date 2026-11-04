"""Auth diagnostics for homologation E2E — no secrets printed."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request


def main() -> int:
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
        token = json.loads(resp.read().decode())["access_token"]
    claims = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))
    iss = claims.get("iss")
    expected = os.environ.get("KEYCLOAK_ISSUER")
    out = {
        "token_iss": iss,
        "env_issuer": expected,
        "issuer_match": iss == expected,
        "azp": claims.get("azp"),
    }
    # Local JWT validate via same library as middleware
    try:
        from delpi_auth.jwt_validator import validate_token

        validate_token(token)
        out["jwt_validate"] = "ok"
    except Exception as exc:  # noqa: BLE001
        out["jwt_validate"] = type(exc).__name__
        out["jwt_validate_msg"] = str(exc)[:200]

    core = os.environ.get("DELPI_AUTH_CORE_API_URL") or os.environ.get(
        "CORE_API_URL"
    )
    out["core_prefix"] = (core or "")[:48]
    if core:
        req = urllib.request.Request(
            f"{core.rstrip('/')}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode())
                out["core_me_status"] = resp.status
                out["core_me_keys"] = sorted(body.keys())[:20]
        except urllib.error.HTTPError as exc:
            out["core_me_status"] = exc.code
            out["core_me_err"] = exc.read()[:160].decode(errors="replace")
        except Exception as exc:  # noqa: BLE001
            out["core_me_error"] = type(exc).__name__
            out["core_me_msg"] = str(exc)[:160]
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
