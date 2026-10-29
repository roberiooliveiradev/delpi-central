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
    ad = orch._providers['mcp']._interop._port._adapter
    cp = ad._credential_provider
    print('known_audiences:', cp._known_resource_audiences)
    print('client_id:', cp._client_id, '| token_url:', cp._token_url, '| host:', cp._host_header)
    for name, prof in ad._connections.items():
        print('profile', name, '| res:', prof.resource_audience, '| xchg:', prof.exchange_audience)
        try:
            cred = cp.credential_for(prof)
            print('   cred ok:', cred[:25])
        except Exception as e:
            print('   EXC:', type(e).__name__, getattr(e,'args',e))
finally:
    unbind_subject_bearer(tok)
