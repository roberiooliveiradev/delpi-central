"""DELIA-C3-GOVERNED-STAGE-RESUME-01 (CP4) live eval — run inside
delpi-delia-api (``/app`` bind-mounted).

Real composed handler (real LLM adapter + real MCP providers wired
from real env) — only the user access context is a fixture, matching
the established eval-script pattern.

  A) resume ON, normal stage timeout — the real chain runs with the
     checkpoint machinery active; a single result is delivered.
  B) resume ON + forced tiny stage timeout — the real model call
     times out; the boundary must emit exactly one CONTINUING
     observation, run at most two governed attempts, and terminate
     PROCESSING_TIMEOUT/model_timeout — never SOURCE_UNAVAILABLE.
  C) resume OFF (legacy) + forced tiny stage timeout — exactly one
     attempt, no CONTINUING.

The API key/bearer is never printed. Output is sanitized JSON.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, "/app")

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.composition.root_composer import (
    _compose_turn_handler,
    _wire_delegated_credential_provider,
    DEFAULT_INTERACTION_MODEL_REF,
)
from app.domain.evidence.model import ModelRef
from app.infrastructure.config.settings import Settings
from app.infrastructure.interoperability.config import (
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.mcp.adapter import (
    McpSpecialistAdapter,
)
from app.infrastructure.model_invocation.openai_compatible_adapter import (
    OpenAICompatibleModelInvocationAdapter,
)


class _CountingAdapter:
    """Delegates every attribute/call to the real adapter — exposure
    policy and mechanics unchanged — and counts invocations per
    task_purpose for the report."""

    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.counts: Counter = Counter()

    def __getattr__(self, name):
        return getattr(self._adapter, name)

    def invoke(self, request):
        self.counts[request.task_purpose_id] += 1
        return self._adapter.invoke(request)


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="cp4-eval",
        name="CP4 Eval",
        email="cp4-eval@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _compose(*, stage_timeout: str, max_attempts: str):
    os.environ["DELIA_MODEL_STAGE_TIMEOUT_SECONDS"] = stage_timeout
    os.environ["DELIA_MAX_GOVERNED_ATTEMPTS"] = max_attempts
    settings = Settings()
    if settings.llm_egress_blocked_reason:
        raise SystemExit(
            f"refused: {settings.llm_egress_blocked_reason}"
        )
    connections = specialist_connections_from_settings(settings)
    interop = SpecialistInterop(
        McpSpecialistAdapter(
            connections,
            credential_provider=_wire_delegated_credential_provider(
                settings, connections
            ),
        )
    )
    adapter = OpenAICompatibleModelInvocationAdapter(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        default_max_output_units=settings.llm_max_output_tokens,
    )
    counting = _CountingAdapter(adapter)
    handler = _compose_turn_handler(
        InvokeModel(counting),
        ModelRef(
            model_id=settings.llm_model,
            version="configured",
            owner_ref="DELPI",
            provider_ref="openai_compatible",
        ),
        interop,
        settings,
        connections,
    )
    return handler, counting


def _run(handler, counting, text: str) -> dict:
    events: list[str] = []
    started = time.monotonic()
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(), input_text=text
        ),
        activity_channel=lambda e: events.append(
            getattr(e.phase, "value", str(e.phase))
        ),
    )
    return {
        "elapsed_s": round(time.monotonic() - started, 2),
        "grounding": str(getattr(result, "grounding_status", "")),
        "model_calls_per_purpose": dict(counting.counts),
        "total_model_calls": sum(counting.counts.values()),
        "continuing_events": events.count("CONTINUING"),
        "phases": events,
        "content_head": (result.content or "")[:80],
    }


def main() -> int:
    question = "Quais painéis existem no VISTA?"
    report: dict[str, dict] = {}

    handler, counting = _compose(stage_timeout="30", max_attempts="2")
    report["A_resume_on_normal"] = _run(handler, counting, question)

    handler, counting = _compose(stage_timeout="2.0", max_attempts="2")
    report["B_resume_on_forced_timeout"] = _run(
        handler, counting, question
    )

    handler, counting = _compose(stage_timeout="2.0", max_attempts="1")
    report["C_legacy_off_forced_timeout"] = _run(
        handler, counting, question
    )

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
