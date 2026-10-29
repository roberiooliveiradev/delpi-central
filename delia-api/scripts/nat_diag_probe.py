import sys, json, hashlib
sys.path.insert(0, '/app')
from scripts.r4_authenticated_resume_eval import _compose
from scripts.semantic_fidelity_eval import _mint_bearer, _find_orchestrator
from app.application.capability_provision import orchestration as O
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

captured = []
orig = orch._propose
def spy(input_text, **kw):
    captured.append({
        'purpose': kw.get('instruction_id'),
        'instruction': kw.get('instruction'),
        'block_payload': kw.get('block_payload'),
    })
    return orig(input_text, **kw)
orch._propose = spy
try:
    groups, failures = orch._groups('natdiag')
    for cid, msg, gid, remote, goal in CASES:
        g = groups[gid]
        caps = {c.remote_name: c for c in g.capabilities}
        cap = caps[remote]
        captured.clear()
        outs = []
        for _ in range(3):
            st = orch._assess_native_path(
                msg, g, cap, correlation='nd-' + cid,
                workspace_context=None, prior_turns=(),
                goal=goal,
                deadline=TurnDeadline.start(180.0))
            outs.append(st)
        blk = captured[0]['block_payload'] if captured else ''
        fp = hashlib.sha256(
            (captured[0]['instruction'] or '' + blk).encode()).hexdigest()[:16] if captured else '?'
        print('==', cid, '->', outs)
        print('   fp:', fp, '| block_chars:', len(blk))
        print('   block:', blk[:1500])
finally:
    orch._propose = orig
    unbind_subject_bearer(tok)
