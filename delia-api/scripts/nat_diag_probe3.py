import sys
sys.path.insert(0, '/app')
from scripts.r4_authenticated_resume_eval import _compose
from scripts.semantic_fidelity_eval import _mint_bearer, _find_orchestrator
from app.application.interaction.turn_budget import TurnDeadline
from app.infrastructure.auth.subject_bearer import bind_subject_bearer, unbind_subject_bearer

handler, _, _ = _compose()
orch = _find_orchestrator(handler)
bearer = _mint_bearer()
tok = bind_subject_bearer(bearer)
TG = orch._TurnGoal
CASES = [
    ('vista_prepare',
     'crie uma playlist chamada testes com a delia',
     'mcp:vista', 'prepare_change',
     TG(goal_class='create_or_modify', business_subject='playlist testes com a delia', declared=True)),
    ('davi_discover',
     'descubra como consultar produtos e traga um terminal bala',
     'mcp:davi', 'discover_delpi_information',
     TG(goal_class='read', business_subject='terminal bala', declared=True)),
    ('teo_latest',
     'Qual o último processo do Transforma+?',
     'mcp:teo', 'record_read',
     TG(goal_class='read', business_subject='último processo do Transforma+', declared=True)),
    ('teo_ctx',
     'use o TÉO para consultar o processo PROC-0105',
     'mcp:teo', 'get_process_context',
     TG(goal_class='read', business_subject='processo PROC-0105', declared=True)),
]
K = 'delia.capability_orchestration.native_assessment'
V29 = '''DECISION RULE - respond "sufficient" unless ALL of these hold:
(1) the goal asks to READ business records, (2) the subject is named
by a descriptive or lay designation rather than an explicit code or
standard identifier, and (3) NONE of the listed capabilities can
resolve the designation - scan the list for DISCOVERY capabilities
(role owner_vocabulary_discovery) and for documentation, guide,
catalog, context, methodology or knowledge READs; if ANY exists, the
owner can resolve the designation itself so the exception does not
apply.
The exception needs ALL three. It NEVER applies to goals that create,
modify, prepare, schedule or commit something inside the owner
application (governed actions are natively self-contained), and NEVER
applies when the selected capability is itself the discovery,
documentation, guide, catalog or knowledge capability of this owner -
those already resolve designations by design. Naming the owner product
is the selected target, not a designation needing resolution.

'''
try:
    groups, _ = orch._groups('natdiag3')
    base = orch._instructions[K]
    v29 = V29 + base[base.index('Decide whether'):]
    for cid, msg, gid, remote, goal in CASES:
        g = groups[gid]
        caps = {c.remote_name: c for c in g.capabilities}
        cap = caps[remote]
        orch._instructions[K] = v29
        outs = []
        for _ in range(4):
            st = orch._assess_native_path(
                msg, g, cap, correlation='nd3-' + cid,
                workspace_context=None, prior_turns=(), goal=goal,
                deadline=TurnDeadline.start(180.0))
            outs.append(st)
        print(cid, 'v29', outs)
finally:
    orch._instructions[K] = base
    unbind_subject_bearer(tok)
