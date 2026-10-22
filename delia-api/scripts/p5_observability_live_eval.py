"""DELIA-UX-CONTEXT-PANEL-EVIDENCE-ACTIVITY-AND-LLM-USAGE-INTEGRATION-01.

Live wire probe for Prompt 5: real Ollama model calls through the real
composed handler, printing the serialized ``observability`` block of
each terminal ``turn_result`` — the exact projection the Context panel
consumes via NDJSON.

Cases:

  A — conversational turn ("olá"): admission may classify it as
      conversation → the handler ``_invoke`` seam records ONE real
      model call with provider-reported usage.
  B — governed turn ("2 exemplos de terminal bala"): the orchestration
      ``_model_stage_proposal`` funnel records every semantic stage
      call; a real read may follow. Under CPU-bound Ollama latency a
      stage timeout is honest evidence too (call counted, usage
      absent — never fabricated).

Output is the already-bounded serialization — no secrets, prompts or
raw payloads are printed.

Environment contract: identical to r4_authenticated_resume_eval.
"""

from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, "/app/delia-api")

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.interaction.handle_interactive_turn import (
    serialize_result,
)
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)

from scripts.r4_authenticated_resume_eval import (
    _compose,
    _context,
    _env,
    _subject_token,
)

CASES = {
    "conversational": "olá, tudo bem?",
    "governed_read": "2 exemplos de terminal bala",
}


def _run(handler, question: str, bearer: str) -> dict:
    events: list[str] = []
    started = time.monotonic()
    binding = bind_subject_bearer(bearer)
    error = None
    wire = None
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(), input_text=question
            ),
            activity_channel=lambda e: events.append(
                getattr(e.phase, "value", str(e.phase))
            ),
        )
        wire = serialize_result(result)
    except Exception as exc:  # honest terminal capture
        error = getattr(exc, "code", type(exc).__name__)
    finally:
        unbind_subject_bearer(binding)
    return {
        "elapsed_s": round(time.monotonic() - started, 2),
        "error": error,
        "phases": events,
        "observability": (wire or {}).get("observability"),
        "grounding_status": (wire or {}).get("grounding_status"),
        # Forbidden-substring gate must hold on the real wire too.
        "wire_forbidden_scan": {
            frag: frag in json.dumps(wire or {})
            for frag in ("provider", "instruction", "system_prompt",
                         "chain_of_thought", "Bearer", "api_key")
        },
    }


def main() -> int:
    for required in ("R4_DEV_USERNAME", "R4_DEV_PASSWORD",
                     "R4_KC_TOKEN_URL"):
        _env(required)
    handler, _guarded, _mcp = _compose()
    out: dict[str, object] = {"cases": {}}
    for name, question in CASES.items():
        out["cases"][name] = _run(handler, question, _subject_token())
    print(json.dumps(out, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
