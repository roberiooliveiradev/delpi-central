import sys, json, traceback, logging
sys.path.insert(0, '/app')
logging.basicConfig(level=logging.DEBUG)
from scripts.r4_authenticated_resume_eval import _compose
from scripts.semantic_fidelity_eval import _mint_bearer, _find_orchestrator
from app.infrastructure.auth.subject_bearer import bind_subject_bearer, unbind_subject_bearer

handler, _, _ = _compose()
orch = _find_orchestrator(handler)
bearer = _mint_bearer()
tok = bind_subject_bearer(bearer)
try:
    prov = orch._providers['mcp']
    interop = prov._interop
    attrs = {a: type(getattr(interop, a)).__name__ for a in dir(interop) if a.startswith('_') and not a.startswith('__')}
    print('interop attrs:', attrs)
    try:
        surface = prov.list_groups(correlation_id='deleg3')
        print('groups:', [g.group_id for g in surface.groups])
        print('failures:', surface.failures)
    except Exception as e:
        traceback.print_exc()
finally:
    unbind_subject_bearer(tok)
