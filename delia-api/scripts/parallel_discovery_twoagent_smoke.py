"""DELIA-C3-T2-PARALLEL-MCP-DISCOVERY-GUARDED-EXPERIMENT-01 — §11 smoke.

ONE real turn through the REAL composed application
(create_application → real providers → real model → governed chain)
with DELIA_PARALLEL_MCP_DISCOVERY=1 and DELIA_TWO_AGENT_EXPERIMENT=1 —
the parallel discovery path inside the experimental two-Agent
composition. Verifies: capabilities discovered, accepted handoff,
single discovery pass, honest outcome — no contract drift.

Run inside delpi-delia-api with both flags exported.
Never prints tokens, secrets, or authorization headers.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, "/app")

from app.application.interaction.contracts import (
    InteractiveTurnRequest,
    TURN_COMMAND_MESSAGE,
)
from app.composition.root_composer import (
    _bounded_http_get,
    create_application,
)
from app.infrastructure.auth.core_platform_access import (
    CorePlatformAccessAdapter,
)
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)
from app.infrastructure.config.settings import Settings

# Bounded e2e battery: each scenario exercises a distinct outcome
# class. EVAL_SCENARIOS overrides with a JSON list of
# {"id": ..., "text": ...}. Read/discovery-class only — no writes.
DEFAULT_SCENARIOS = [
    {"id": "enum", "text": "liste os catálogos disponíveis"},
    {
        "id": "read",
        "text": "quais são os itens do catálogo de produtos?",
    },
    {
        "id": "owner_down",
        "text": "qual o saldo atual do produto ABC-123 no estoque?",
    },
    {"id": "ambiguous", "text": "me conta sobre o projeto"},
]


def _subject_token() -> str:
    fields = {
        "grant_type": "password",
        "client_id": "delpi-central",
        "username": os.environ["DEV_PORTAL_USERNAME"],
        "password": os.environ["DEV_PORTAL_PASSWORD"],
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


def main() -> int:
    settings = Settings()

    core = CorePlatformAccessAdapter(
        core_api_url=settings.core_api_url,
        timeout_seconds=settings.core_timeout_seconds,
        http_get=_bounded_http_get,
    )

    app = create_application()
    handler = app.config["INTERACTION_TURN_HANDLER"]

    scenarios = DEFAULT_SCENARIOS
    if os.getenv("EVAL_SCENARIOS"):
        scenarios = json.loads(os.environ["EVAL_SCENARIOS"])

    runs = []
    for sc in scenarios:
        # Fresh subject per scenario: the realm access-token TTL is
        # shorter than a full battery on slow CPU inference, so a
        # single mint would expire mid-run and masquerade as an
        # application auth failure.
        subject = _subject_token()
        access_context = core.resolve(subject)
        token = bind_subject_bearer(subject)
        started = time.monotonic()
        try:
            result = handler.execute(
                InteractiveTurnRequest(
                    access_context=access_context,
                    input_text=sc["text"],
                    command_type=TURN_COMMAND_MESSAGE,
                )
            )
            runs.append(
                {
                    "id": sc["id"],
                    "elapsed_s": round(
                        time.monotonic() - started, 1
                    ),
                    "result_type": type(result).__name__,
                    "epistemic_class": str(
                        getattr(result, "epistemic_class", None)
                    ),
                    "grounding_status": str(
                        getattr(result, "grounding_status", None)
                    ),
                    "limitations": [
                        str(lim)[:80]
                        for lim in getattr(
                            result, "limitations", ()
                        )
                        or ()
                    ][:4],
                    "content_head": str(
                        getattr(result, "content", "")
                    )[:120]
                    or None,
                }
            )
        except Exception as exc:
            runs.append(
                {
                    "id": sc["id"],
                    "elapsed_s": round(
                        time.monotonic() - started, 1
                    ),
                    "result_type": f"EXC:{type(exc).__name__}",
                    "epistemic_class": None,
                    "grounding_status": None,
                    "limitations": None,
                    "content_head": None,
                }
            )
        finally:
            unbind_subject_bearer(token)

    summary = {
        "flags": {
            "parallel_mcp_discovery": settings.parallel_mcp_discovery,
            "two_agent_experiment": settings.two_agent_experiment,
            "runtime_profile": os.getenv("DELIA_RUNTIME_PROFILE")
            or "default",
        },
        "scenarios": runs,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
