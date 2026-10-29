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
    port = orch._providers['mcp']._interop._port
    ad = port._adapter
    attrs = {a: type(getattr(ad,a)).__name__ for a in dir(ad) if a.startswith('_') and not a.startswith('__')}
    print('adapter attrs:', attrs)
    for a,t in attrs.items():
        obj = getattr(ad,a)
        if isinstance(obj, dict):
            print(a, '->', {k: type(v).__name__ for k,v in obj.items()})
        elif hasattr(obj, 'credential_for'):
            print('delegator:', a, '->', {x: type(getattr(obj,x)).__name__ for x in dir(obj) if x.startswith('_') and not x.startswith('__')})
finally:
    unbind_subject_bearer(tok)
