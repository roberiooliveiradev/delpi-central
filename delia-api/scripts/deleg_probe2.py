import sys, json, traceback
sys.path.insert(0, '/app')
from scripts.r4_authenticated_resume_eval import _compose
from scripts.semantic_fidelity_eval import _mint_bearer, _find_orchestrator
from app.infrastructure.auth.subject_bearer import bind_subject_bearer, unbind_subject_bearer

handler, _, _ = _compose()
orch = _find_orchestrator(handler)
bearer = _mint_bearer()
tok = bind_subject_bearer(bearer)
try:
    prov = orch._providers['mcp']
    attrs = {a: type(getattr(prov, a)).__name__ for a in dir(prov) if a.startswith('_') and not a.startswith('__')}
    print('provider attrs:', attrs)
    for name, t in attrs.items():
        obj = getattr(prov, name)
        if hasattr(obj, 'credential_for'):
            print('delegator:', name)
finally:
    unbind_subject_bearer(tok)
