"""DELIA-C3-T2-PARALLEL-MCP-DISCOVERY-GUARDED-EXPERIMENT-01 — real A/B.

Sequential (flag OFF) vs bounded parallel (flag ON) discovery inside
``McpCapabilityProvider.list_groups`` against the REAL approved
specialists, using the REAL governed seams:

* subject bearer minted via Keycloak password grant (DEV_PORTAL_*),
  bound on the caller thread via ``bind_subject_bearer`` — the same
  seam production injects at composition;
* real ``KeycloakDelegatedCredentialProvider`` token exchange, real
  ``SpecialistInterop`` + ``DelpiMcpTransport`` absolute deadlines;
* per-specialist delegated credential verified post-run: each cache
  entry's ``sub`` must equal the caller subject (no identity mixing).

Run inside delpi-delia-api: ``python scripts/parallel_mcp_discovery_ab_eval.py``.
Never prints tokens, secrets, or authorization headers.
"""

from __future__ import annotations

import base64
import json
import os
import statistics
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, "/app")

from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.composition.root_composer import _bounded_http_get
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    current_subject_bearer,
    unbind_subject_bearer,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.http.deadline_transport import deadline_http_post
from app.infrastructure.interoperability.config import (
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.delegation import (
    InMemoryDelegatedTokenCache,
    KeycloakDelegatedCredentialProvider,
)
from app.infrastructure.interoperability.mcp.adapter import (
    McpSpecialistAdapter,
)

REPEATS = 4
TURN_TIMEOUT_SECONDS = 30.0


def _claims(jwt: str) -> dict:
    return json.loads(
        base64.urlsafe_b64decode(jwt.split(".")[1] + "==")
    )


def _subject_token() -> str:
    """Password grant, client delpi-central — same eval minting the
    prior instrumented evals used (DEV_PORTAL_* credentials)."""
    fields = {
        "grant_type": "password",
        "client_id": "delpi-central",
        "username": os.environ["DEV_PORTAL_USERNAME"],
        "password": os.environ["DEV_PORTAL_PASSWORD"],
        # ``openid`` is REQUIRED: MCP resource servers challenge with
        # scope="openid profile email mcp:tools" — without it the
        # exchanged delegated credential 401s with insufficient_scope.
        "scope": "openid profile email",
    }
    req = urllib.request.Request(
        "http://delpi-gateway/auth/realms/delpi/protocol/openid-connect/token",
        data=urllib.parse.urlencode(fields).encode(),
        headers={"Host": "localhost"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())[
        "access_token"
    ]


def _credential_provider(settings: Settings, profiles):
    from delpi_auth.jwt_validator import validate_token

    return KeycloakDelegatedCredentialProvider(
        token_url=settings.exchange_token_url,
        client_id=settings.exchange_client_id,
        client_secret=settings.exchange_client_secret,
        timeout_seconds=settings.exchange_timeout_seconds,
        http_post=deadline_http_post,
        # REAL accessor — the worker-visible ContextVar seam, not a
        # lambda: proves the production binding path end to end.
        subject_bearer_getter=current_subject_bearer,
        token_validator=validate_token,
        cache=InMemoryDelegatedTokenCache(
            max_ttl_seconds=settings.delegated_token_ttl_seconds
        ),
        known_resource_audiences=frozenset(
            p.resource_audience for p in profiles.values()
        ),
        host_header=settings.exchange_host_header,
    )


def _run_once(provider, specialist_ids) -> dict:
    started = time.monotonic()
    surface = provider.list_groups(
        correlation_id="ab-eval", timeout_seconds=TURN_TIMEOUT_SECONDS
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    caps = sum(len(g.capabilities) for g in surface.groups)
    return {
        "elapsed_ms": elapsed_ms,
        "groups": sorted(f"{g.provider_id}:{g.group_id}" for g in surface.groups),
        "capabilities_total": caps,
        "failures": list(surface.failures),
        "specialists_ok": len(surface.groups),
        "specialists_total": len(specialist_ids),
    }


def main() -> int:
    settings = Settings()
    profiles = specialist_connections_from_settings(settings)
    # Constant specialist set across BOTH arms. Default: enabled
    # profiles; EVAL_SPECIALISTS narrows to a healthy subset when one
    # specialist is environmentally degraded (documented, not hidden).
    narrow = os.getenv("EVAL_SPECIALISTS")
    specialist_ids = (
        tuple(s for s in narrow.split(",") if s in profiles)
        if narrow
        else tuple(
            sid
            for sid, p in profiles.items()
            if p.enabled and p.endpoint
        )
    )
    subject = _subject_token()
    subject_sub = _claims(subject).get("sub", "")

    token = bind_subject_bearer(subject)
    runs: dict[str, list[dict]] = {"sequential": [], "parallel": []}
    adapters = {}
    try:
        for mode, parallel in (
            ("sequential", False),
            ("parallel", True),
        ):
            # Fresh adapter + credential cache PER ARM — a shared warm
            # cache would bias the second arm (each arm warms its own,
            # mirroring a cold turn against a fresh provider chain).
            adapters[mode] = McpSpecialistAdapter(
                profiles,
                credential_provider=_credential_provider(
                    settings, profiles
                ),
            )
            interop = SpecialistInterop(adapters[mode])
            provider = McpCapabilityProvider(
                interop,
                specialist_ids,
                parallel_discovery=parallel,
                subject_bearer_getter=current_subject_bearer,
                bind_bearer=bind_subject_bearer,
                unbind_bearer=unbind_subject_bearer,
            )
            for _ in range(REPEATS):
                runs[mode].append(_run_once(provider, specialist_ids))
                time.sleep(0.2)
        # Identity isolation check runs while the bearer is STILL
        # bound — after unbind, credential_for legitimately fails
        # closed (no identity), which is not a leak signal.
        cred_provider = None
        for attr in ("_credential_provider", "credential_provider"):
            cred_provider = getattr(
                adapters["parallel"], attr, None
            )
            if cred_provider is not None:
                break
        subj_ok = "not_checked"
        if cred_provider is not None:
            checks = {}
            for sid in specialist_ids:
                try:
                    delegated_tok = cred_provider.credential_for(
                        profiles[sid]
                    )
                    checks[sid] = (
                        _claims(delegated_tok).get("sub") == subject_sub
                    )
                except Exception:
                    checks[sid] = False
            subj_ok = all(checks.values())
    finally:
        unbind_subject_bearer(token)

    delegated_tok = None  # sanitize: never reuse bearer material

    def _lat(rs):
        return [r["elapsed_ms"] for r in rs]

    report = {
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "specialists": list(specialist_ids),
        "repeats": REPEATS,
        "subject_resolved_sub_present": bool(subject_sub),
        "delegated_credentials_same_subject": subj_ok,
        "worker_bearer_leak": current_subject_bearer() is not None,
        "sequential": {
            "runs": runs["sequential"],
            "latencies_ms": _lat(runs["sequential"]),
            "p50_ms": statistics.median(_lat(runs["sequential"])),
            "max_ms": max(_lat(runs["sequential"])),
            "auth_failures": sum(
                1
                for r in runs["sequential"]
                for f in r["failures"]
                if f == "mcp_authentication_failed"
            ),
        },
        "parallel": {
            "runs": runs["parallel"],
            "latencies_ms": _lat(runs["parallel"]),
            "p50_ms": statistics.median(_lat(runs["parallel"])),
            "max_ms": max(_lat(runs["parallel"])),
            "auth_failures": sum(
                1
                for r in runs["parallel"]
                for f in r["failures"]
                if f == "mcp_authentication_failed"
            ),
        },
        "catalog_equivalence": all(
            runs["parallel"][i]["groups"]
            == runs["sequential"][i]["groups"]
            and runs["parallel"][i]["capabilities_total"]
            == runs["sequential"][i]["capabilities_total"]
            for i in range(REPEATS)
        ),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
