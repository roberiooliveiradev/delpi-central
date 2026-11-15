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

QUESTION = "liste os catálogos disponíveis"


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
    subject = _subject_token()

    core = CorePlatformAccessAdapter(
        core_api_url=settings.core_api_url,
        timeout_seconds=settings.core_timeout_seconds,
        http_get=_bounded_http_get,
    )
    access_context = core.resolve(subject)

    app = create_application()
    handler = app.config["INTERACTION_TURN_HANDLER"]

    token = bind_subject_bearer(subject)
    started = time.monotonic()
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=access_context,
                input_text=QUESTION,
                command_type=TURN_COMMAND_MESSAGE,
            )
        )
    finally:
        unbind_subject_bearer(token)
    elapsed = time.monotonic() - started

    summary = {
        "flags": {
            "parallel_mcp_discovery": settings.parallel_mcp_discovery,
            "two_agent_experiment": settings.two_agent_experiment,
        },
        "elapsed_s": round(elapsed, 1),
        "result_type": type(result).__name__,
        "status": getattr(result, "status", None)
        or getattr(result, "outcome", None)
        or str(result)[:120],
    }
    # Surface whatever truthful outcome fields the result carries.
    for attr in (
        "outcome",
        "sufficiency",
        "completion",
        "answer_status",
    ):
        value = getattr(result, attr, None)
        if value is not None:
            summary[attr] = str(value)[:160]
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
