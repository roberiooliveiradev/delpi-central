"""C3-MCP-INTEROP-01 live connectivity eval — run inside delpi-delia-api.

For each approved specialist (DAVI/TÉO/VISTA):

1. transport probe — unauthenticated POST initialize; 401 challenge
   proves reachability + fail-closed OAuth surface;
2. authenticated catalog — tools/list via SpecialistInterop using a
   user-delegated credential exchanged from the subject bearer supplied
   in DELIA_EVAL_SUBJECT_TOKEN (eval-only injection point); absent
   subject bearer reports AUTH_FAIL_CLOSED (expected when no
   delegation exists).

Never prints tokens. Exit code 0 always — results are in the report.
"""

from __future__ import annotations

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


def _eval_credential_provider(settings: Settings, profiles):
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
        subject_bearer_getter=lambda: os.getenv("DELIA_EVAL_SUBJECT_TOKEN"),
        token_validator=validate_token,
        cache=InMemoryDelegatedTokenCache(
            max_ttl_seconds=settings.delegated_token_ttl_seconds
        ),
        known_resource_audiences=frozenset(
            p.resource_audience for p in profiles.values()
        ),
    )


def main() -> int:
    settings = Settings()
    profiles = specialist_connections_from_settings(settings)
    adapter = McpSpecialistAdapter(
        profiles, credential_provider=_eval_credential_provider(settings, profiles)
    )
    interop = SpecialistInterop(adapter)
    report: dict[str, dict] = {}
    for specialist_id in SPECIALISTS:
        profile = profiles[specialist_id]
        entry: dict[str, object] = {
            "configured": bool(profile.endpoint),
            "enabled": profile.enabled,
            "resource_audience_bound": bool(profile.resource_audience),
            "subject_bearer_present": bool(
                os.getenv("DELIA_EVAL_SUBJECT_TOKEN")
            ),
        }
        if profile.endpoint:
            entry["transport_probe"] = probe_transport(profile.endpoint)
        try:
            catalog = interop.discover_catalog(
                SpecialistCatalogRequest(
                    specialist_id=specialist_id, correlation_id="eval-c3"
                )
            )
            entry["catalog"] = {
                "status": "PASS",
                "invocable": [c.remote_name for c in catalog.capabilities],
                "blocked": list(catalog.blocked_remote_names),
            }
            tool, args = PROBE_TOOL[specialist_id]
            outcome = interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=specialist_id,
                    remote_capability=tool,
                    correlation_id="eval-c3",
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
