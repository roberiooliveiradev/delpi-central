"""Goal-handoff live probe — NOT committed (task scratch).

Drives the real composed chain (real Ollama adapter via _compose)
across the C1/C2 scenario matrix. For every selection-stage request
it extracts the catalog block and records: JSON validity, length vs
MAX_SURFACE_CHARS, business_subject presence/integrity.

Usage: c3_goal_handoff_probe.py <scenario>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.application.capability_provision.orchestration import (
    MAX_SURFACE_CHARS,
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

_BLOCK_RE = re.compile(
    r"<(capability_groups|capabilities|foreign_capability_groups)"
    r">(.*?)</\1>",
    re.DOTALL,
)

# C3: capture EVERY block tag per request — projection integrity is a
# cross-stage property, not only selection.
_ANY_BLOCK_RE = re.compile(
    r"<(capability_groups|capabilities|foreign_capability_groups|"
    r"resolver|records|evidence|schema|capability|owner_index|"
    r"missing_inputs|analysis_continuation|"
    r"target_capability_group)>(.*?)</\1>",
    re.DOTALL,
)


def _user(text: str) -> ConversationContextTurn:
    return ConversationContextTurn(
        kind=TurnKind.USER_INPUT, content=text
    )


def _result(text: str, cls: EpistemicClass | None):
    return ConversationContextTurn(
        kind=TurnKind.DELIA_RESULT,
        content=text,
        epistemic_class=cls,
    )


_SCENARIOS: dict[str, tuple[str, tuple[ConversationContextTurn, ...]]] = {
    "three_records": (
        "Traga três exemplos de terminal bala.",
        (),
    ),
    "o2": (
        "O que é o terminal O2?",
        (),
    ),
    "pino": (
        "Me dê dois exemplos de terminal pino.",
        (),
    ),
    "ref_user": (
        # referent authored by the USER in an earlier turn — lawful
        # business_subject derivation under the v21 contract.
        "me mostre dois exemplos do segundo tipo",
        (
            _user(
                "Liste os tipos de terminal disponíveis, como o "
                "terminal pino."
            ),
            _result(
                "Encontrei 3 tipos: terminal bala, terminal pino e "
                "terminal forquilha.",
                EpistemicClass.CALCULATION,
            ),
        ),
    ),
    "ref_assistant_only": (
        # referent only exists in DELIA_RESULT prose — NOT a lawful
        # business_subject source; CALCULATION gates observation out.
        "me mostre dois exemplos do segundo tipo",
        (
            _user("Liste os tipos de terminal disponíveis."),
            _result(
                "Encontrei 3 tipos: terminal bala, terminal pino e "
                "terminal forquilha.",
                EpistemicClass.CALCULATION,
            ),
        ),
    ),
    "ref_observation": (
        # OBSERVATION prior — prior_observation channel carries the
        # referent to selection stages.
        "me mostre dois exemplos do segundo tipo",
        (
            _user("Liste os tipos de terminal disponíveis."),
            _result(
                "Encontrei 3 tipos: terminal bala, terminal pino e "
                "terminal forquilha.",
                EpistemicClass.OBSERVATION,
            ),
        ),
    ),
    "subject_change": (
        "agora me mostre dois exemplos de cliente",
        (
            _user("Liste os tipos de terminal disponíveis."),
            _result(
                "Encontrei 3 tipos de terminal.",
                EpistemicClass.OBSERVATION,
            ),
        ),
    ),
}


def main() -> int:
    scenario = sys.argv[1] if len(sys.argv) > 1 else "ref_user"
    question, prior = _SCENARIOS[scenario]

    handler, guarded, mcp = _compose()
    real_invoke = guarded.invoke
    probe: list[dict] = []

    def recording(request):
        text = getattr(request, "input_text", "") or ""
        for tag, block in _ANY_BLOCK_RE.findall(text):
            entry = {
                "purpose": request.task_purpose_id,
                "block_tag": tag,
                "block_len": len(block),
            }
            try:
                parsed = json.loads(block)
                entry["json_valid"] = True
                if isinstance(parsed, dict):
                    markers = {
                        k: v
                        for k, v in parsed.items()
                        if k.endswith("_omitted") and v
                    }
                    if markers:
                        entry["omissions"] = markers
            except Exception:
                entry["json_valid"] = False
            probe.append(entry)
        if request.task_purpose_id in SELECTION_PURPOSES:
            text = getattr(request, "input_text", "") or ""
            entry: dict = {"purpose": request.task_purpose_id}
            match = _BLOCK_RE.search(text)
            if match:
                block = match.group(2)
                entry["block_len"] = len(block)
                entry["under_max"] = len(block) <= MAX_SURFACE_CHARS
                try:
                    parsed = json.loads(block)
                    entry["json_valid"] = True
                    is_dict = isinstance(parsed, dict)
                    body = (
                        (
                            parsed.get("capability_groups")
                            or parsed.get("capabilities")
                        )
                        if is_dict
                        else parsed
                    )
                    entry["catalog_items"] = (
                        len(body) if isinstance(body, list) else None
                    )
                    entry["has_subject"] = (
                        is_dict and "business_subject" in parsed
                    )
                    entry["subject_whole"] = (
                        parsed.get("business_subject") if is_dict else None
                    )
                    entry["has_observation"] = (
                        is_dict and "prior_observation" in parsed
                    )
                except Exception:
                    entry["json_valid"] = False
            else:
                entry["block_found"] = False
            probe.append(entry)
        payload = real_invoke(request)
        usage = getattr(payload, "usage", None)
        if usage is not None:
            probe.append(
                {
                    "purpose": request.task_purpose_id,
                    "usage": {
                        "input": getattr(
                            usage, "input_units", None
                        ),
                        "output": getattr(
                            usage, "output_units", None
                        ),
                    },
                    "duration_ms": getattr(
                        payload, "duration_ms", None
                    ),
                }
            )
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

    try:
        bearer = Path("/tmp/eval_bearer").read_text().strip()
    except OSError:
        bearer = "probe-no-token"
    binding = bind_subject_bearer(bearer)
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
                "scenario": scenario,
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
                )[:400],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
