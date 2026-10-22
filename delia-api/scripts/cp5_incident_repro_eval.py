"""DELIA-C3-GOVERNED-STAGE-RESUME-INDEPENDENT-VERIFICATION-01 (CP5/§7).

P1/P2 incident reproduction against the real composed handler:
real LLM adapter + real MCP surface adapters, governed resume ON at
the authorized dev profile. The typed incident questions are replayed
verbatim — including the typo in P2.

  P1: "qual o ultimo processo cadastrado no transformometro?"
  P2: "quais oa ultimos processos cadastrados?"

Without a delegated user bearer the provider invoke leg fails closed
(credentials unavailable at call time) — that boundary is recorded
honestly per-question rather than masked. Model stages, owner/capability
selection, stage reuse and terminal semantics are real.

No tokens, secrets or payload values are printed — only bounded
identifiers and outcome metadata.
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

P1_QUESTION = "qual o ultimo processo cadastrado no transformometro?"
P2_QUESTION = "quais oa ultimos processos cadastrados?"


class _CountingAdapter:
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
        user_id="cp5-eval",
        name="CP5 Eval",
        email="cp5-eval@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _compose():
    os.environ.setdefault("DELIA_MAX_GOVERNED_ATTEMPTS", "2")
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
        "question": text,
        "elapsed_s": round(time.monotonic() - started, 2),
        "grounding": str(getattr(result, "grounding_status", "")),
        "model_calls_per_purpose": dict(counting.counts),
        "continuing_events": events.count("CONTINUING"),
        "phases": events,
        "content_head": (result.content or "")[:120],
    }


def main() -> int:
    report: dict[str, dict] = {}
    for label, question in (
        ("P1_last_registered_process", P1_QUESTION),
        ("P2_last_registered_processes_typo", P2_QUESTION),
    ):
        handler, counting = _compose()
        report[label] = _run(handler, counting, question)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
