"""R01 — live interaction-admission semantic eval (bounded).

Replays ``_admit_conversational_turn`` on the real composed
orchestrator with the shipped (or override) admission instruction.
Captures classification + owner-path decision without running the
MCP investigation Agent — so admission accuracy can be measured
separately from tool-calling.

Env:
  DEV_PORTAL_USERNAME / DEV_PORTAL_PASSWORD / KEYCLOAK_URL — required
  DELIA_RUNTIME_PROFILE — optional process-scoped profile override
  DELIA_ADMISSION_INSTRUCTION_PATH — optional JSON resource override
  DELIA_EVAL_SCENARIOS_JSON — optional scenario list
  DELIA_EVAL_REPS — repetitions per scenario (default 1)

Never prints secrets.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.environ.get("DELIA_APP_ROOT", "/app"))

from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.domain.interaction.model import TurnKind
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)
from app.infrastructure.config.cri_instruction_resource import (
    load_orchestration_instructions,
)
from app.infrastructure.config.settings import Settings
from app.application.capability_provision.semantic_capability_support import (
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    ORCHESTRATION_INSTRUCTION_KEYS,
)
from scripts.native_mcptoolset_direct_eval import (  # noqa: E402
    _compose,
    _subject_token,
)


STAGE_BUDGET_S = 90.0


def _find_admission_orchestrator(handler):
    """Locate the governed orchestrator that owns admission.

    The historical semantic_fidelity finder required
    ``_select_capability``; the native-first orchestrator keeps
    ``_admit_conversational_turn`` + ``_propose`` instead.
    """
    seen: set[int] = set()
    stack = [handler]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        if hasattr(node, "_admit_conversational_turn") and hasattr(
            node, "_propose"
        ):
            return node
        if hasattr(node, "__dict__"):
            stack.extend(
                value
                for value in vars(node).values()
                if hasattr(value, "__dict__")
            )
    return None

DEFAULT_SCENARIOS = [
    {"id": "C1", "question": "processos na engenharia", "expect_owner": True},
    {"id": "B1", "question": "analise departamento engenharia", "expect_owner": True},
    {"id": "CONC_SIPOC", "question": "O que é SIPOC?", "expect_owner": False},
    {
        "id": "CONC_PDCA",
        "question": "Explique o método PDCA de forma geral.",
        "expect_owner": False,
    },
    {
        "id": "OPS_NON_TEO_1",
        "question": "Quais iniciativas estão registradas?",
        "expect_owner": True,
    },
    {
        "id": "OPS_NON_TEO_2",
        "question": "Compare os resultados das filiais.",
        "expect_owner": True,
    },
    {
        "id": "AMB_1",
        "question": "melhoria na engenharia",
        "expect_owner": True,
    },
    {
        "id": "SURFACE",
        "question": "O que você pode consultar?",
        "expect_owner": None,  # surface path — not owner MCP
    },
]


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _scenarios():
    raw = _env("DELIA_EVAL_SCENARIOS_JSON")
    if not raw:
        return list(DEFAULT_SCENARIOS)
    data = json.loads(raw)
    return list(data)


def _question_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _owner_path(interaction_class: str | None, owner_required: bool) -> bool:
    # Mirror investigation engine: class not None and not surface →
    # conversational; owner_required True with class None → investigation.
    if interaction_class == "surface_inquiry":
        return False
    return bool(owner_required) and interaction_class is None


def _apply_instruction_override(orch) -> str:
    path = _env("DELIA_ADMISSION_INSTRUCTION_PATH")
    if not path:
        # Read version from the orchestrator's loaded text lineage when
        # available via the resource file beside the app config.
        cfg = Path(
            os.environ.get(
                "DELIA_ORCH_INSTRUCTIONS_PATH",
                "/app/config/orchestration_instructions.delpi.json",
            )
        )
        if cfg.is_file():
            data = json.loads(cfg.read_text(encoding="utf-8"))
            return str(data.get("version") or "unknown")
        return "unknown"
    loaded = load_orchestration_instructions(
        path, required_names=ORCHESTRATION_INSTRUCTION_KEYS
    )
    orch._instructions = dict(loaded.instructions)
    return loaded.version


def _admit(orch, text: str, prior=()):
    return orch._admit_conversational_turn(
        text,
        workspace_context=None,
        prior_turns=tuple(prior),
        correlation="r01-adm-eval",
        deadline=TurnDeadline.start(STAGE_BUDGET_S),
    )


def main() -> int:
    # Admission-only: no MCP invoke. Subject bearer is optional and
    # used only when portal credentials are present and mintable.
    reps = int(_env("DELIA_EVAL_REPS") or "1")
    settings = Settings()
    if settings.llm_egress_blocked_reason:
        print(f"refused: {settings.llm_egress_blocked_reason}")
        return 2
    handler, _mcp = _compose()
    orch = _find_admission_orchestrator(handler)
    if orch is None:
        print("orchestrator_absent")
        return 3
    instruction_version = _apply_instruction_override(orch)

    bound = False
    if (
        _env("DEV_PORTAL_USERNAME")
        and _env("DEV_PORTAL_PASSWORD")
        and _env("KEYCLOAK_URL")
    ):
        try:
            bind_subject_bearer(_subject_token())
            bound = True
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "auth_bind": "skipped",
                        "reason": type(exc).__name__,
                    }
                )
            )
    rows = []
    try:
        for spec in _scenarios():
            sid = str(spec["id"])
            question = str(spec["question"])
            expect = spec.get("expect_owner")
            prior_raw = spec.get("prior") or []
            prior = tuple(
                ConversationContextTurn(
                    kind=(
                        TurnKind.USER_INPUT
                        if str(role).lower() in ("user", "user_input")
                        else TurnKind.DELIA_RESULT
                    ),
                    content=content,
                )
                for role, content in prior_raw
            )
            decisions = []
            for _ in range(reps):
                t0 = time.perf_counter()
                interaction_class, owner_required = _admit(
                    orch, question, prior=prior
                )
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                owner = _owner_path(interaction_class, owner_required)
                decisions.append(
                    {
                        "interaction_class": interaction_class,
                        "owner_required_flag": owner_required,
                        "owner_path": owner,
                        "latency_ms": elapsed_ms,
                    }
                )
            owner_flags = [d["owner_path"] for d in decisions]
            if expect is None:
                correct = None
            else:
                correct = all(flag is bool(expect) for flag in owner_flags)
            row = {
                "scenario": sid,
                "question_hash": _question_hash(question),
                "expect_owner_path": expect,
                "decisions": decisions,
                "correct": correct,
            }
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False))
    finally:
        if bound:
            unbind_subject_bearer()

    out = {
        "task_id": "DELIA-C3-R01-SEMANTIC-ADMISSION-OPERATIONAL-CLASSIFICATION-REMEDIATION-01",
        "model": settings.llm_model,
        "runtime_profile": settings.runtime_profile,
        "config_fingerprint": settings.runtime_config_fingerprint,
        "instruction_id": INTERACTION_ADMISSION_INSTRUCTION_ID,
        "instruction_version": instruction_version,
        "reps": reps,
        "rows": rows,
        "pass_count": sum(1 for r in rows if r["correct"] is True),
        "fail_count": sum(1 for r in rows if r["correct"] is False),
        "unscored_count": sum(1 for r in rows if r["correct"] is None),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
