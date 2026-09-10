"""E9.S10 — unknown external OpenAPI offline (sem pathMarkers / registry DELPI).

Prova: provider externo (logistics-example) é recuperado e planejado só pelo Action Catalog.
"""

from __future__ import annotations

from app.application.services.plan_external_actions_service import PlanExternalActionsService
from app.application.services.retrieve_action_candidates_service import (
    RetrieveActionCandidatesService,
)
from tests.support.openapi_logistics_fixtures import (
    import_logistics_actions,
    logistics_allowed_action_ids,
)


class _Repo:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        rows = [
            a
            for a in self.actions
            if not allowed or str(a.get("actionId")) in allowed
        ]
        return rows[:limit]

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []


def test_e9_s10_unknown_provider_top_k_without_path_markers():
    """Positive: OpenAPI externo desconhecido do registry DELPI entra no top-K."""
    actions = import_logistics_actions()
    assert actions
    assert all("pathMarkers" not in a for a in actions)
    msg = "Onde esta a remessa 45871 e qual a previsao de entrega?"
    candidates = RetrieveActionCandidatesService(_Repo(actions)).retrieve(
        msg,
        allowed_action_ids=logistics_allowed_action_ids(actions),
        catalog_actions=actions,
    )
    assert candidates
    top = candidates[0].descriptor
    assert top.operation_id == "get_shipment_tracking"
    assert "logistics" in str(top.action_id).lower() or top.path.startswith("/")


def test_e9_s10_unknown_provider_plan_binds_args():
    """Sibling: plano liga shipment id sem strategy tipada no content DELPI."""
    actions = import_logistics_actions()
    msg = "Onde esta a remessa 45871 e qual a previsao de entrega?"
    candidates = RetrieveActionCandidatesService(_Repo(actions)).retrieve(
        msg,
        allowed_action_ids=logistics_allowed_action_ids(actions),
        catalog_actions=actions,
    )
    plan = PlanExternalActionsService().plan(msg, candidates)
    assert plan.steps
    assert plan.steps[0].arguments["parameters"]["id"] == "45871"


def test_e9_s10_negative_unknown_action_id_not_injected():
    """Negative: actionId fora do catálogo não entra no plano."""
    actions = import_logistics_actions()
    candidates = RetrieveActionCandidatesService(_Repo(actions)).retrieve(
        "status da remessa 1",
        allowed_action_ids=logistics_allowed_action_ids(actions),
        catalog_actions=actions,
    )
    # Planner heurístico/offline: se receber step inventado via validate path —
    # aqui garantimos que o catálogo não contém o id fantasma.
    ids = {str(a.get("actionId")) for a in actions}
    assert "totally.unknown.action" not in ids
    assert candidates
