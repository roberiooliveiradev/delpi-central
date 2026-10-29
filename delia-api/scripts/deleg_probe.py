import sys, json
sys.path.insert(0, "/app")
from scripts.r4_authenticated_resume_eval import _compose
from scripts.semantic_fidelity_eval import _mint_bearer, _find_orchestrator
from app.infrastructure.auth.subject_bearer import bind_subject_bearer, unbind_subject_bearer

handler, _, _ = _compose()
orch = _find_orchestrator(handler)
bearer = _mint_bearer()
tok = bind_subject_bearer(bearer)
try:
    for pid, prov in orch._providers.items():
        try:
            surface = prov.list_groups(correlation_id="deleg-probe")
            print(pid, "groups:", [g.group_id for g in surface.groups], "failures:", surface.failures)
        except Exception as e:
            print(pid, "EXC:", type(e).__name__, str(e)[:300])
finally:
    unbind_subject_bearer(tok)
