"""DELIA-C3-T2-POST-E2-REAL-MODEL-FUNCTIONAL-RECOVERY-01 — live eval.

Runs the RQ-1 scenario matrix through the REAL composed application
(create_application → real MCP owners → real model → governed chain)
inside the delpi-delia-api container:

    DELIA_RUNTIME_PROFILE=local_ollama \
        python scripts/post_e2_real_model_eval.py

Fresh subject token per scenario (realm TTL is shorter than a slow-CPU
battery). Read/discovery only — never WRITE, never prints tokens or
secrets. Binds results to git HEAD + runtime profile.
"""

from __future__ import annotations

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

# RQ-1 matrix (A-D) + controls. Portuguese inputs mirror the live
# operator surface; all are READ-class intents.
DEFAULT_SCENARIOS = [
    # Case A — direct product lookup (RQ-1)
    {"id": "A_direct_product",
     "text": "Qual a descrição do produto de código 90260147?"},
    # Case B — product structure (RQ-1)
    {"id": "B_product_structure",
     "text": "Mostre a estrutura do produto 90260921."},
    # Case C — paged listing (RQ-1)
    {"id": "C_paged_listing",
     "text": "Liste os produtos ativos do catálogo."},
    # Case D — multi-evidence investigation (RQ-1)
    {"id": "D_multi_evidence",
     "text": ("Consulte o produto 90260147 e depois mostre a estrutura "
              "do produto 90260921 para comparar os dois.")},
    # Ambiguity control — must not fabricate a capability
    {"id": "amb_control",
     "text": "me conta uma novidade"},
    # No-capability control — expected honest NON_GROUNDED/limited
    {"id": "nocap_control",
     "text": "qual a previsão do tempo para amanhã?"},
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
        subject = _subject_token()
        access_context = core.resolve(subject)
        token = bind_subject_bearer(subject)
        started = time.monotonic()
        rec = {"id": sc["id"], "text": sc["text"][:60]}
        try:
            result = handler.execute(
                InteractiveTurnRequest(
                    access_context=access_context,
                    input_text=sc["text"],
                    command_type=TURN_COMMAND_MESSAGE,
                )
            )
            attempts = getattr(result, "governed_attempts", None) or ()
            usage = getattr(result, "usage", None) or {}
            rec.update(
                elapsed_s=round(time.monotonic() - started, 1),
                result_type=type(result).__name__,
                status=str(getattr(result, "status", None)),
                epistemic_class=str(
                    getattr(result, "epistemic_class", None)
                ),
                grounding_status=str(
                    getattr(result, "grounding_status", None)
                ),
                governed_attempts=len(attempts),
                attempt_statuses=[
                    str(getattr(a, "status", "?")).split(".")[-1]
                    for a in attempts
                ][:8],
                limitations=[
                    str(lim)[:90]
                    for lim in getattr(result, "limitations", ()) or ()
                ][:4],
                usage=usage,
                content_head=str(getattr(result, "content", ""))[:200]
                or None,
            )
        except Exception as exc:  # noqa: BLE001 — eval records honestly
            rec.update(
                elapsed_s=round(time.monotonic() - started, 1),
                result_type=f"EXC:{type(exc).__name__}",
                error=str(exc)[:200],
            )
        finally:
            unbind_subject_bearer(token)
        runs.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)

    try:
        head = (
            __import__("subprocess")
            .check_output(["git", "rev-parse", "HEAD"], cwd="/app")
            .decode()
            .strip()
        )
    except Exception:
        head = os.getenv("EVAL_RECORDED_HEAD") or "unknown"
    summary = {
        "head": head,
        "runtime_profile": os.getenv("DELIA_RUNTIME_PROFILE") or "default",
        "llm_model": settings.llm_model,
        "two_agent_experiment": settings.two_agent_experiment,
        "parallel_mcp_discovery": settings.parallel_mcp_discovery,
        "scenarios": [r["id"] for r in runs],
        "outcomes": {
            r["id"]: {
                k: r[k]
                for k in (
                    "result_type",
                    "grounding_status",
                    "governed_attempts",
                    "elapsed_s",
                )
                if k in r
            }
            for r in runs
        },
    }
    print("=== SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
