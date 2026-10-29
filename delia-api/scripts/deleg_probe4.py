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
    port = prov._interop._port
    print('port attrs:', {a: type(getattr(port,a)).__name__ for a in dir(port) if a.startswith('_') and not a.startswith('__')})
    for a in dir(port):
        if a.startswith('_') and not a.startswith('__'):
            obj = getattr(port, a)
            if hasattr(obj, 'credential_for'):
                print('delegator found:', a)
                profiles = getattr(port, '_profiles', None) or getattr(obj, '_profiles', None)
                print('profiles:', profiles)
                # find profiles via interop connections
finally:
    unbind_subject_bearer(tok)
