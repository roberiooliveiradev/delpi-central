"""C3-MCP-INTEROP-01R1B live connectivity eval — run inside delpi-delia-api.

Authenticated specialist discovery proof per approved specialist
(DAVI/TÉO/VISTA):

1. transport probe — unauthenticated POST initialize; 401 challenge
   proves reachability + fail-closed OAuth surface;
2. authenticated catalog — real Portal subject bearer
   (DELIA_EVAL_SUBJECT_TOKEN) → DÉLIA token exchange → same-user
   resource-bound credential → initialize + tools/list via
   SpecialistInterop.discover_catalog → DÉLIA classification
   projection (DISCOVERY eligible; READ/PREPARE/ACT/unknown blocked);
3. optional C3-safe DISCOVERY call (DAVI discover_delpi_information,
   TÉO/VISTA get_catalog) — never a business READ.

The eval also proves the subject bearer resolves through real Core
/me before any specialist interaction (sanitized output only).

Never prints tokens, secrets, or authorization headers.
Exit code 0 always — results are in the report.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time

import requests

sys.path.insert(0, "/app")

from app.application.specialist_interop.contracts import (
    SpecialistCatalogRequest,
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import SpecialistInteropError
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.specialist_interop.rules import operation_class_for
from app.infrastructure.auth.core_platform_access import (
    CorePlatformAccessAdapter,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.interoperability.config import (
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.delegation import (
    InMemoryDelegatedTokenCache,
    KeycloakDelegatedCredentialProvider,
)
from app.infrastructure.interoperability.mcp.adapter import McpSpecialistAdapter
from app.infrastructure.interoperability.mcp.transport import (
    MCP_PROTOCOL_VERSION,
)

SPECIALISTS = ("davi", "teo", "vista")
PROBE_TOOL = {
    "davi": ("discover_delpi_information", {"query": "catalog smoke"}),
    "teo": ("get_catalog", {}),
    "vista": ("get_catalog", {}),
}
ALL_RESOURCE_AUDS = {
    "https://minhadelpi.com.br/apps/api-delpi/mcp",
    "https://minhadelpi.com.br/apps/transformometro-api/mcp",
    "https://minhadelpi.com.br/apps/tv-dashboard-api/mcp",
}


def _claims(jwt: str) -> dict:
    return json.loads(
        base64.urlsafe_b64decode(jwt.split(".")[1] + "==")
    )


def probe_transport(endpoint: str) -> dict:
    started = time.monotonic()
    try:
        response = requests.post(
            endpoint,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "delia-eval", "version": "0"},
                    },
                }
            ),
            timeout=10,
        )
        return {
            "reachable": True,
            "status": response.status_code,
            "latency_ms": int((time.monotonic() - started) * 1000),
            "auth_challenge": "WWW-Authenticate" in response.headers,
        }
    except requests.RequestException as exc:
        return {"reachable": False, "error": type(exc).__name__}


def _eval_credential_provider(settings: Settings, profiles, subject: str):
    """Eval-only wiring: subject bearer from DELIA_EVAL_SUBJECT_TOKEN."""
    if not (
        settings.exchange_token_url
        and settings.exchange_client_id
        and settings.exchange_client_secret
    ):
        return None
    from delpi_auth.jwt_validator import validate_token

    return KeycloakDelegatedCredentialProvider(
        token_url=settings.exchange_token_url,
        client_id=settings.exchange_client_id,
        client_secret=settings.exchange_client_secret,
        timeout_seconds=settings.exchange_timeout_seconds,
        http_post=requests.post,
        subject_bearer_getter=lambda: subject,
        token_validator=validate_token,
        cache=InMemoryDelegatedTokenCache(
            max_ttl_seconds=settings.delegated_token_ttl_seconds
        ),
        known_resource_audiences=frozenset(
            p.resource_audience for p in profiles.values()
        ),
        host_header=settings.exchange_host_header,
    )


def _prove_core_context(settings: Settings, subject: str) -> dict:
    """Real Core /me resolution for the subject bearer (sanitized)."""
    adapter = CorePlatformAccessAdapter(
        core_api_url=settings.core_api_url,
        timeout_seconds=settings.core_timeout_seconds,
        http_get=requests.get,
    )
    try:
        ctx = adapter.resolve(subject)
    except Exception as exc:
        return {"resolved": False, "error": type(exc).__name__}
    return {
        "resolved": True,
        "user_sub_present": bool(ctx.user_id),
        "roles": len(ctx.roles or ()),
        "effective_permissions": len(ctx.effective_permissions or ()),
        "is_superadmin": bool(ctx.is_superadmin),
    }


def main() -> int:
    settings = Settings()
    profiles = specialist_connections_from_settings(settings)
    subject = (os.getenv("DELIA_EVAL_SUBJECT_TOKEN") or "").strip()
    subject_claims = _claims(subject) if subject.count(".") == 2 else {}
    subject_sub = subject_claims.get("sub", "")

    report: dict[str, object] = {
        "core_context": (
            _prove_core_context(settings, subject)
            if subject
            else {"resolved": False, "error": "missing_subject_bearer"}
        ),
    }

    provider = _eval_credential_provider(settings, profiles, subject)
    adapter = McpSpecialistAdapter(profiles, credential_provider=provider)
    interop = SpecialistInterop(adapter)

    for specialist_id in SPECIALISTS:
        profile = profiles[specialist_id]
        entry: dict[str, object] = {
            "configured": bool(profile.endpoint),
            "enabled": profile.enabled,
            "resource_audience": profile.resource_audience,
        }
        if profile.endpoint:
            entry["transport_probe"] = probe_transport(profile.endpoint)

        # Delegated credential claims (sanitized booleans only)
        if provider is not None and subject:
            try:
                delegated = provider.credential_for(profile)
                dc = _claims(delegated)
                auds = dc.get("aud")
                auds = auds if isinstance(auds, list) else [auds]
                entry["delegated_credential"] = {
                    "same_sub": dc.get("sub") == subject_sub,
                    "azp_is_requester": dc.get("azp") == settings.exchange_client_id,
                    "resource_audience_bound": profile.resource_audience in auds,
                    "foreign_mcp_audiences": sorted(
                        a for a in auds
                        if a in ALL_RESOURCE_AUDS
                        and a != profile.resource_audience
                    ),
                    "mcp_tools_scope": "mcp:tools"
                    in str(dc.get("scope") or ""),
                    "exp_valid": dc.get("exp", 0) > int(time.time()),
                }
            except SpecialistInteropError as exc:
                entry["delegated_credential"] = {"status": exc.code}

        try:
            catalog = interop.discover_catalog(
                SpecialistCatalogRequest(
                    specialist_id=specialist_id, correlation_id="eval-c3-r1b"
                )
            )
            unknown = [
                name
                for name in (
                    list(catalog.blocked_remote_names)
                    + [c.remote_name for c in catalog.capabilities]
                )
                if operation_class_for(specialist_id, name) is None
            ]
            entry["catalog"] = {
                "status": "PASS",
                "authenticated_initialize": True,
                "authenticated_tools_list": True,
                "remote_tool_count": len(catalog.capabilities)
                + len(catalog.blocked_remote_names),
                "approved_discovery": [
                    c.remote_name for c in catalog.capabilities
                ],
                "blocked_count": len(catalog.blocked_remote_names),
                "unknown_remote_names": unknown,
            }
            tool, args = PROBE_TOOL[specialist_id]
            outcome = interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=specialist_id,
                    remote_capability=tool,
                    correlation_id="eval-c3-r1b",
                    arguments=args,
                )
            )
            entry["discovery_call"] = {
                "status": "PASS",
                "is_complete": outcome.is_complete,
                "bytes": len(outcome.content_text),
            }
        except SpecialistInteropError as exc:
            entry["catalog"] = {"status": exc.code}
        report[specialist_id] = entry
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
