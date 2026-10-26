"""Goal-handoff live probe — NOT committed (task scratch).

Drives the real composed chain (real Ollama adapter via _compose)
on the referential scenario that demonstrated the goal-continuity
loss: a referential follow-up whose prior result is NOT
OBSERVATION-class, so prior_observation is intentionally empty.
Captures whether business_subject reaches each selection payload.
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "/app")

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import TurnKind
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)

from scripts.r4_authenticated_resume_eval import _compose, _context

SELECTION_PURPOSES = {
    "delia.capability_orchestration.select_group",
    "delia.capability_orchestration.select_capability",
    "delia.capability_orchestration.foreign_selection",
}


def main() -> int:
    handler, guarded, mcp = _compose()
    real_invoke = guarded.invoke
    probe: list[dict] = []

    def recording(request):
        if request.task_purpose_id in SELECTION_PURPOSES:
            text = getattr(request, "input_text", "") or ""
            probe.append(
                {
                    "purpose": request.task_purpose_id,
                    "has_business_subject_key": '"business_subject"'
                    in text,
                    "subject_value_present": "terminal" in text.lower(),
                }
            )
        payload = real_invoke(request)
        if request.task_purpose_id == (
            "delia.capability_orchestration.turn_goal"
        ):
            probe.append(
                {
                    "purpose": "turn_goal_output",
                    "structured_output": getattr(
                        payload, "structured_output", None
                    ),
                }
            )
        return payload

    guarded.invoke = recording

    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "me mostre dois exemplos do segundo tipo"
    )
    cold = len(sys.argv) > 2 and sys.argv[2] == "cold"
    prior: tuple[ConversationContextTurn, ...] = ()
    if not cold:
        prior = (
            ConversationContextTurn(
                kind=TurnKind.USER_INPUT,
                content="Liste os tipos de terminal disponíveis.",
            ),
            ConversationContextTurn(
                kind=TurnKind.DELIA_RESULT,
                content=(
                    "Encontrei 3 tipos: terminal bala, terminal pino e "
                    "terminal forquilha."
                ),
                epistemic_class=EpistemicClass.CALCULATION,
            ),
        )
    binding = bind_subject_bearer("probe-no-token")
    result = None
    error = None
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(),
                input_text=question,
                prior_turns=prior,
            )
        )
    except Exception as exc:  # noqa: BLE001 - probe records code only
        error = getattr(exc, "code", type(exc).__name__)
    finally:
        unbind_subject_bearer(binding)

    print(
        json.dumps(
            {
                "error": error,
                "message_kind": getattr(result, "message_kind", None),
                "grounding": str(
                    getattr(result, "grounding_status", "")
                ),
                "stages": [
                    c["purpose"] for c in guarded.calls
                ],
                "stage_errors": [
                    {
                        "purpose": c["purpose"],
                        "error": c.get("error"),
                    }
                    for c in guarded.calls
                    if c.get("error")
                ],
                "selection_probe": probe,
                "mcp_invoke_targets": list(mcp.invoke_targets),
                "content_head": (
                    getattr(result, "content", "") or ""
                )[:300],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
