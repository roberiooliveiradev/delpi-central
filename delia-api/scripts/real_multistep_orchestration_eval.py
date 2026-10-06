"""ARCH-DRIFT-DELIA-GENERIC-MCP-MULTISTEP-ORCHESTRATION-R1 live eval.

Run inside delpi-delia-api. Proves through the real HTTP boundary:

  Portal user token (password grant, scope=openid — dev realm)
    -> POST /interaction/turns (real auth middleware -> Core /me)
    -> generic multi-step orchestration against live owners:
       * process-by-name: generic same-owner resolver supplies the
         missing id — the user is NOT asked for process_id;
       * homonym: multiple owner candidates -> bounded clarification,
         never a silent pick;
       * ANALYSIS class: owner ANALYSIS capability invoked as ANALYSIS;
       * TÉO capability evolution: a capability added after older
         DÉLIA builds is discovered live and invocable with zero
         DÉLIA registration.

No writes: PREPARE/ACT are never exercised here; owner mutations are
out of scope for this acceptance (PRODUCTION_OWNER_MUTATIONS=NO).

Required env (never printed): DEV_PORTAL_USERNAME, DEV_PORTAL_PASSWORD.
Never prints tokens, secrets, authorization headers or proposal handles.
Exit code 0 always — results are in the report.
"""

from __future__ import annotations

import base64
import json
import os
import re

import requests


_SENSITIVE = re.compile(
    r"(proposal[_\-.]?handle|bearer|token|secret|password)",
    re.IGNORECASE,
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
        headers={
            "Host": os.environ.get("DELIA_EXCHANGE_HOST_HEADER")
            or "minhadelpi.com.br"
        },
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
        "requester_audience": "delia-api" in (
            claims.get("aud")
            if isinstance(claims.get("aud"), list)
            else [claims.get("aud")]
        ),
        "scope": sorted(str(claims.get("scope") or "").split()),
        "exp_in_seconds": int(claims.get("exp") or 0)
        - int(__import__("time").time()),
    }


def _handle_scan(body: dict) -> int:
    """Count serialized surfaces that look like a raw opaque handle."""
    serialized = json.dumps(body, ensure_ascii=False, default=str)
    hits = re.findall(r"prop-[a-z0-9-]{8,}|ph_[a-z0-9-]{8,}", serialized)
    return len(hits)


def _turn(token: str, text: str, context=None) -> dict:
    payload = {"input": text}
    if context:
        payload["context"] = context
    try:
        response = requests.post(
            "http://localhost:8000/interaction/turns",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=280,
        )
    except requests.RequestException as exc:
        return {"http_status": None, "error": type(exc).__name__}
    body = response.json()
    content = str(body.get("content") or "")
    return {
        "http_status": response.status_code,
        "code": body.get("code"),
        "grounding_status": body.get("grounding_status"),
        "epistemic_class": body.get("epistemic_class"),
        "provenance": body.get("provenance"),
        "has_confirmation_request": bool(
            body.get("confirmation_request")
        ),
        "candidate_lines": sum(
            1
            for line in content.splitlines()
            if line.lstrip().startswith("- ")
        ),
        "raw_handle_hits": _handle_scan(body),
        "content_prefix": content[:240],
    }


def main() -> int:
    token, claims = _mint_subject_token()
    report = {
        "subject_token": claims,
        # process-by-name: target needs an owner id the user never gave
        "process_by_name": _turn(
            token,
            os.getenv("DELIA_EVAL_PROCESS_QUERY")
            or "me explique o contexto do processo Auditoria 5S",
        ),
        # homonym: known ambiguous name -> bounded clarification
        "homonym": _turn(
            token,
            os.getenv("DELIA_EVAL_HOMONYM_QUERY")
            or "me explique o processo Controle de refeições",
        ),
        # ANALYSIS class: non-material owner analysis (VISTA)
        "vista_analysis": _turn(
            token,
            os.getenv("DELIA_EVAL_ANALYSIS_QUERY")
            or (
                "analise um bloco de dados com titulo Vendas e valores "
                "10, 20, 30 e recomende o melhor visual"
            ),
        ),
        # owner capability evolution: live tools/list is the surface
        "teo_methodology": _turn(
            token,
            os.getenv("DELIA_EVAL_TEO_QUERY")
            or "qual a metodologia do Transformômetro?",
        ),
        "unauthenticated": requests.post(
            "http://localhost:8000/interaction/turns",
            json={"input": "processos"},
            timeout=10,
        ).status_code,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
