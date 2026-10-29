"""Native-assessment replay: does the over-fire persist across the
three live goal shapes? v27 shipped vs variant candidates."""
import sys, json
sys.path.insert(0, "/app")
from scripts.r4_authenticated_resume_eval import _compose, _context
from scripts.semantic_fidelity_eval import _mint_bearer, _find_orchestrator
from app.application.interaction.turn_budget import TurnDeadline
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer, unbind_subject_bearer,
)

STAGE = 60.0
REPS = 3

CASES = [
    ("vista_prepare", "crie uma playlist chamada testes com a delia",
     "mcp:vista", "prepare_change"),
    ("davi_discover", "descubra como consultar produtos e traga um terminal bala",
     "mcp:davi", "discover_delpi_information"),
    ("teo_latest", "Qual o último processo do Transforma+?",
     "mcp:teo", "record_read"),
    ("teo_guide", "use o mcp teo para consultar o processo mais recente",
     "mcp:teo", "get_methodology_guide"),
]

VARIANT = """DECISION RULE - respond "sufficient" unless ALL of these hold:
(1) the goal asks to READ business records, (2) the subject is named
by a descriptive or lay designation rather than an explicit code or
standard identifier, and (3) NONE of the listed capabilities can
resolve the designation - scan the list for documentation, guide,
catalog, context, methodology or knowledge READs; if ANY exists, the
owner can resolve the designation itself so the exception does not
apply.
The exception needs ALL three. It NEVER applies to goals that create,
modify, prepare, schedule or commit something inside the owner
application (governed actions are natively self-contained), and NEVER
applies when the selected capability is itself the documentation,
discovery, guide, catalog or knowledge read of this owner - those
already resolve designations by design. Naming the owner product is
the selected target, not a designation needing resolution.

"""

def main():
    bearer = _mint_bearer()
    handler, _, _ = _compose()
    orch = _find_orchestrator(handler)
    tok = bind_subject_bearer(bearer)
    try:
        surface = {}
        for pid, prov in orch._providers.items():
            s = prov.list_groups(correlation_id="nat-probe")
            for g in getattr(s, "groups", ()):
                surface[f"{pid}:{g.group_id}"] = g
        base_inst = orch._instructions["delia.capability_orchestration.native_assessment"]
        for cid, msg, gid, remote in CASES:
            g = surface.get(gid)
            if g is None:
                print(cid, "GROUP_ABSENT"); continue
            caps = {c.remote_name: c for c in g.capabilities}
            cap = caps.get(remote)
            if cap is None:
                print(cid, "CAP_ABSENT", sorted(caps)); continue
            for label, inst in (("v27", base_inst), ("v28", VARIANT + base_inst.split("\n\n",1)[1])):
                orch._instructions["delia.capability_orchestration.native_assessment"] = inst
                outs = []
                for _ in range(REPS):
                    st = orch._assess_native_path(
                        msg, g, cap, correlation="natp",
                        workspace_context=None, prior_turns=(),
                        deadline=TurnDeadline.start(STAGE))
                    outs.append(getattr(st, "value", st))
                print(cid, label, outs)
            orch._instructions["delia.capability_orchestration.native_assessment"] = base_inst
    finally:
        unbind_subject_bearer(tok)
    return 0

if __name__ == "__main__":
    sys.exit(main())
