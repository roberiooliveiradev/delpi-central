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
    ('legit_foreign_product_on_teo',
     'quais produtos estao cadastrados no sistema',
     'mcp:teo', 'record_read',
     TG(goal_class='read', business_subject='produtos cadastrados', declared=True)),
    ('corroboration',
     'confirme com uma segunda fonte se o processo PROC-0105 existe',
     'mcp:teo', 'record_read',
     TG(goal_class='read', business_subject='processo PROC-0105', comparison_requested=True, declared=True)),
    ('cross_domain',
     'o processo PROC-0105 esta vinculado a quais playlists do dashboard',
     'mcp:teo', 'record_read',
     TG(goal_class='read', business_subject='playlists vinculadas ao PROC-0105', declared=True)),
]
K = 'delia.capability_orchestration.native_assessment'
RULE = '''DECISION RULE - respond "sufficient" unless ALL of these hold:
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
application - governed actions are natively self-contained, and
missing user-supplied details are clarified with the user, never
supplied by foreign evidence. It NEVER applies when the selected
capability is itself the discovery, documentation, guide, catalog or
knowledge capability of this owner - those already resolve
designations by design. Ordering, listing or filtering over the
owner own records (latest, most recent, all, count) is a native
owner query, not a foreign designation problem. Naming the owner
product is the selected target, not a designation needing
resolution.'''
try:
    groups, _ = orch._groups('natdiag6')
    base = orch._instructions[K]
    body = base[base.index('Decide whether'):]
    v31 = body + '\n\n' + RULE + '\n'
    for cid, msg, gid, remote, goal in CASES:
        g = groups[gid]
        caps = {c.remote_name: c for c in g.capabilities}
        cap = caps[remote]
        orch._instructions[K] = v31
        outs = []
        for _ in range(3):
            st = orch._assess_native_path(
                msg, g, cap, correlation='nd6-' + cid,
                workspace_context=None, prior_turns=(), goal=goal,
                deadline=TurnDeadline.start(180.0))
            outs.append(st)
        print(cid, 'v31', outs)
finally:
    orch._instructions[K] = base
    unbind_subject_bearer(tok)
