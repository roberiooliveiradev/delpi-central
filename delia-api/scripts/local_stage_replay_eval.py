"""Task 16 — deterministic stage-level replay.

Isolates the proven first divergences from
local_orchestration_reliability_eval.py by replaying single model
stages directly on the REAL composed orchestrator:

- ``_admit_conversational_turn`` — admission classification
  (Incidents A + B: refusal/hallucination before owner path).
- ``_assess_native_path`` + ``_select_foreign_capability`` —
  the ord_latest foreign fan-out chain.

Admission is also replayed against an *instruction variant* (same
typed contract: requires_owner_surface + interaction_class) to test
whether a semantics-preserving restructure changes small-model
compliance — never a lexical route, still a model proposal.

Run inside the delia-api container:
    python -m scripts.local_stage_replay_eval [reps]
"""
from __future__ import annotations

import json
import sys
import time

from scripts.r4_authenticated_resume_eval import _compose, _context  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    _find_orchestrator,
    _mint_bearer,
)
from app.application.interaction.turn_budget import (  # noqa: E402
    TurnDeadline,
)
from app.application.interaction.workspace_context import (  # noqa: E402
    WorkspaceContext,
)
from app.infrastructure.auth.subject_bearer import (  # noqa: E402
    bind_subject_bearer,
    unbind_subject_bearer,
)

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
STAGE_BUDGET_S = 120.0

INTERACTION_ADMISSION_INSTRUCTION_ID = (
    "delia.capability_orchestration.interaction_admission"
)
FOREIGN_SELECTION_INSTRUCTION_ID = (
    "delia.capability_orchestration.foreign_selection"
)

ADMISSION_BLOCK = (
    '{"owner_surfaces":"live governed owner surfaces exist; their '
    'catalog is listed only after admission - decide whether the '
    'request requires governed owner data or can be answered '
    'conversationally"}'
)

WS_TV = WorkspaceContext(
    host_app_id="tv-dashboard",
    route="/apps/tv-dashboard/",
    view_ref=None,
    selected_entity_ref=None,
    entity_refs=(),
)

# --- admission battery: (id, text, workspace, expected_owner_path) ---
# expected_owner_path=True means requires_owner_surface=true OR
# class in {operational, ambiguous} — the typed owner-path decision.
ADMISSION_CASES = [
    ("adm_b_pino", "2 exemplos de terminal pino", None, True),
    ("adm_b_bala", "Me dê dois exemplos de terminal bala", None, True),
    ("adm_b_faston", "Liste 3 tipos de conector faston", None, True),
    ("adm_b_abstract", "2 exemplos de sentimento", None, False),
    (
        "adm_b_fictional",
        "Invente dois exemplos de planetas imaginários",
        None,
        False,
    ),
    (
        "adm_a_playlist_ws",
        "Crie uma playlist chamada testes com a delia",
        WS_TV,
        True,
    ),
    (
        "adm_a_playlist_nows",
        "Crie uma playlist chamada testes com a delia",
        None,
        True,
    ),
    (
        "adm_a_paineis",
        "Quero criar uma programação nova no Painéis TV",
        WS_TV,
        True,
    ),
    (
        "adm_ord_latest",
        "Qual o último processo do Transforma+?",
        None,
        True,
    ),
    (
        "adm_c_explicit_teo",
        "Use o TÉO para consultar o processo PROC-0105",
        None,
        True,
    ),
    ("adm_ctrl_oi", "oi", None, False),
    ("adm_ctrl_sipoc", "O que é SIPOC?", None, False),
    ("adm_ctrl_surface", "O que você pode consultar?", None, False),
]


def _replay_admission(orch, text, ws, instruction=None):
    """Replicates _admit_conversational_turn's proposal + decision
    mapping with an overrideable instruction text."""
    instr = instruction or orch._instruction(
        INTERACTION_ADMISSION_INSTRUCTION_ID
    )
    proposal = orch._propose(
        text,
        block_tag="admission",
        block_payload=ADMISSION_BLOCK,
        instruction_id=INTERACTION_ADMISSION_INSTRUCTION_ID,
        instruction=instr,
        expected_fields=(
            "requires_owner_surface",
            "interaction_class",
        ),
        input_kind="interaction_admission",
        allowed_keys=frozenset(
            {
                "requires_owner_surface",
                "interaction_class",
                "limitations",
            }
        ),
        workspace_context=ws,
        prior_turns=(),
        correlation="replay-adm",
        deadline=TurnDeadline.start(STAGE_BUDGET_S),
    )
    if not isinstance(proposal, dict):
        return None, None
    raw_req = proposal.get("requires_owner_surface")
    requires = (
        raw_req is True
        or (isinstance(raw_req, str) and raw_req.strip().lower() == "true")
    )
    cls = proposal.get("interaction_class")
    cls = cls.strip().lower() if isinstance(cls, str) else None
    return requires, cls


def _owner_path(requires, cls):
    """Mirrors orchestration.py owner-path gate (line ~10677)."""
    return requires or cls in {"operational", "ambiguous"}


def _admission_battery(orch, instruction=None, label="v26"):
    rows = []
    for case_id, text, ws, expect_owner in ADMISSION_CASES:
        decisions = []
        for _ in range(REPS):
            req, cls = _replay_admission(orch, text, ws, instruction)
            decisions.append({"requires": req, "class": cls})
        got = [_owner_path(r["requires"], r["class"]) for r in decisions]
        rows.append(
            {
                "case": case_id,
                "instruction": label,
                "expect_owner_path": expect_owner,
                "decisions": decisions,
                "owner_path": got,
                "correct": all(g == expect_owner for g in got),
            }
        )
    return rows


# v27 candidate — same typed contract (requires_owner_surface +
# interaction_class, identical class vocabulary), restructured so
# the owner-path decision rule leads and the everyday-life trap is
# named once. Semantic remediation at the instruction's legitimate
# owner (versioned resource), not a lexical route.
V27_CANDIDATE = json.load(
    open("/app/config/orchestration_instructions.delpi.json")
)["instructions"]["delia.capability_orchestration.interaction_admission"]


def _native_foreign_replay(orch, groups):
    """Replays the ord_latest chain's native_assessment +
    foreign_selection on the live surface."""
    rows = []
    teo = groups.get("mcp:teo")
    if teo is None:
        return [{"error": "teo group absent"}]
    caps = {
        c.remote_name: c
        for c in teo.capabilities
    }
    # What the model selected live vs the listing capability:
    for remote in ("get_process_timeline", "record_read"):
        desc = caps.get(remote)
        if desc is None:
            continue
        statuses = []
        for _ in range(REPS):
            st = orch._assess_native_path(
                "Qual o último processo do Transforma+?",
                teo,
                desc,
                correlation="replay-nat",
                workspace_context=None,
                prior_turns=(),
                deadline=TurnDeadline.start(STAGE_BUDGET_S),
            )
            statuses.append(st)
        rows.append(
            {
                "stage": "native_assessment",
                "target_capability": remote,
                "statuses": statuses,
            }
        )
    # foreign selection — only legitimate when native declared need;
    # replay it to see what the model WOULD pick if forced there.
    picks = []
    for _ in range(REPS):
        sel = orch._select_foreign_capability(
            "Qual o último processo do Transforma+?",
            groups,
            "mcp:teo",
            mode="evidence",
            correlation="replay-for",
            workspace_context=None,
            prior_turns=(),
            deadline=TurnDeadline.start(STAGE_BUDGET_S),
            business_subject="Transforma+",
        )
        picks.append(
            None
            if sel is None
            else f"{sel[0]}.{sel[1].capability_id}"
        )
    rows.append(
        {
            "stage": "foreign_selection",
            "picks": picks,
        }
    )
    return rows


def main() -> int:
    bearer = _mint_bearer()
    token = bind_subject_bearer(bearer)
    try:
        handler, _, _ = _compose()
        orch = _find_orchestrator(handler)
        assert orch is not None, "orchestrator not found"
        t0 = time.monotonic()
        deadline = TurnDeadline.start(120)
        groups, failures = orch._groups("replay-groups", deadline)
        group_report = {
            k: len(g.capabilities) for k, g in groups.items()
        }
        print("GROUPS", json.dumps(group_report))
        if failures:
            print("GROUP_FAILURES", json.dumps(failures))

        out = {
            "admission_v26": None,
            "admission_v27": None,
            "native_foreign": None,
        }
        out["admission_v26"] = _admission_battery(orch)
        out["admission_v27"] = _admission_battery(
            orch, V27_CANDIDATE, label="v27"
        )
        out["native_foreign"] = _native_foreign_replay(orch, groups)
        out["elapsed_s"] = round(time.monotonic() - t0, 1)
        print("RESULT " + json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    finally:
        unbind_subject_bearer(token)


if __name__ == "__main__":
    raise SystemExit(main())
