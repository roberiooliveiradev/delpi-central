"""DELIA-C3-OLLAMA-ONLY-LOCAL-LLM-TESTING-01 — real Ollama functional eval.

Runs the real composed handler (real OpenAI-compatible adapter pointed at
the local Ollama /v1 endpoint, real MCP surface adapters, governed resume
at the authorized dev profile) against the operational reference
questions:

  O1: "qual o ultimo processo cadastrado?"
  O2: "2 exemplos de terminal bala"
  O3: "use o davi"
  O4: "o mcp davi"
  O5: O1 again with DELIA_RESPONSE_INTELLIGENCE_ENABLED=0 (CRI OFF)

Records per model-stage: call count, wall time, token units, finish
status and the bounded structured decision; plus phases/CONTINUING events
and the terminal grounding. The specialist invoke leg fails closed
without a delegated bearer — recorded honestly per question.

Requires DELIA_LLM_* pointing at the local Ollama endpoint; the script
refuses external endpoints before any socket is opened
(settings.llm_egress_blocked_reason) — there is no paid fallback.
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

QUESTIONS = (
    ("O1_last_process", "qual o ultimo processo cadastrado?"),
    ("O2_terminal_bala", "2 exemplos de terminal bala"),
    ("O3_use_davi", "use o davi"),
    ("O4_mcp_davi", "o mcp davi"),
)


class _MeasuringAdapter:
    """Records per-purpose call count, wall time and usage units."""

    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.counts: Counter = Counter()
        self.calls: list[dict] = []

    def __getattr__(self, name):
        return getattr(self._adapter, name)

    def invoke(self, request):
        self.counts[request.task_purpose_id] += 1
        started = time.monotonic()
        try:
            payload = self._adapter.invoke(request)
        except Exception as exc:
            self.calls.append(
                {
                    "purpose": request.task_purpose_id,
                    "ms": int((time.monotonic() - started) * 1000),
                    "error": getattr(exc, "code", type(exc).__name__),
                }
            )
            raise
        usage = getattr(payload, "usage", None)
        structured = getattr(payload, "structured_output", {}) or {}
        self.calls.append(
            {
                "purpose": request.task_purpose_id,
                "ms": int((time.monotonic() - started) * 1000),
                "finish": str(getattr(payload, "finish_status", "")),
                "in_units": getattr(usage, "input_units", None),
                "out_units": getattr(usage, "output_units", None),
                "decision": {
                    str(k): str(v)[:160] for k, v in structured.items()
                },
            }
        )
        return payload


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="ollama-eval",
        name="Ollama Eval",
        email="ollama-eval@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _compose(cri: bool = True):
    os.environ.setdefault("DELIA_MAX_GOVERNED_ATTEMPTS", "2")
    os.environ["DELIA_RESPONSE_INTELLIGENCE_ENABLED"] = "1" if cri else "0"
    settings = Settings()
    if settings.llm_egress_blocked_reason:
        raise SystemExit(f"refused: {settings.llm_egress_blocked_reason}")
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
    measuring = _MeasuringAdapter(adapter)
    handler = _compose_turn_handler(
        InvokeModel(measuring),
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
    return handler, measuring


def _run(handler, measuring, text: str) -> dict:
    events: list[str] = []
    started = time.monotonic()
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(), input_text=text
            ),
            activity_channel=lambda e: events.append(
                getattr(e.phase, "value", str(e.phase))
            ),
        )
    except Exception as exc:
        return {
            "question": text,
            "elapsed_s": round(time.monotonic() - started, 2),
            "terminal": "EXCEPTION",
            "error": str(exc)[:200],
            "model_calls": measuring.calls,
            "continuing_events": events.count("CONTINUING"),
            "phases": events,
        }
    return {
        "question": text,
        "elapsed_s": round(time.monotonic() - started, 2),
        "grounding": str(getattr(result, "grounding_status", "")),
        "status": str(getattr(result, "status", "")),
        "model_calls": measuring.calls,
        "continuing_events": events.count("CONTINUING"),
        "phases": events,
        "content_head": (result.content or "")[:160],
    }


def main() -> int:
    settings_probe = Settings()
    report: dict = {
        "model": settings_probe.llm_model,
        "base_url": settings_probe.llm_base_url,
        "environment": settings_probe.environment,
        "questions": {},
    }
    for label, question in QUESTIONS:
        handler, measuring = _compose(cri=True)
        report["questions"][label] = _run(handler, measuring, question)
    handler, measuring = _compose(cri=False)
    report["questions"]["O5_cri_off_control"] = _run(
        handler, measuring, QUESTIONS[0][1]
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
