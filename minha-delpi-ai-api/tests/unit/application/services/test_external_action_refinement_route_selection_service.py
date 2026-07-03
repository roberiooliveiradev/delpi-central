from types import SimpleNamespace

from app.application.services.external_actions.external_action_refinement_route_selection_service import (
    ExternalActionRefinementRouteSelectionService,
)


class _ParentsOutsideCandidateSliceRepo:
    parents_action = {
        "actionId": "api_delpi.products.get_product_parents",
        "method": "GET",
        "path": "/products/{code}/parents",
        "operationId": "get_product_parents",
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True},
            {"name": "page", "in": "query"},
            {"name": "page_size", "in": "query"},
        ],
    }

    def __init__(self):
        self.lookup_calls = 0
        self.candidate_calls = 0

    def get_action_for_execution(self, action_id: str):
        self.lookup_calls += 1

        if action_id == self.parents_action["actionId"]:
            return {"action": self.parents_action}

        return None

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        self.candidate_calls += 1
        filler = [
            {
                "actionId": f"api_delpi.filler.action_{index}",
                "method": "GET",
                "path": f"/filler/{index}",
                "parametersSchema": [],
            }
            for index in range(limit)
        ]

        return filler


def test_build_pagination_action_resolves_action_by_id_when_not_in_first_candidates():
    repo = _ParentsOutsideCandidateSliceRepo()
    service = ExternalActionRefinementRouteSelectionService(repo)
    refinement = SimpleNamespace(
        action_id="api_delpi.products.get_product_parents",
        page=2,
        page_size=None,
        previous_parameters={"code": "10080022", "page": 1, "page_size": 200},
        reason=None,
    )
    allowed = ["api_delpi.products.get_product_parents"] + [
        f"api_delpi.filler.action_{index}" for index in range(120)
    ]

    selected = service.build_pagination_action(
        refinement,
        action_id="api_delpi.products.get_product_parents",
        allowed_action_ids=allowed,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "api_delpi.products.get_product_parents"
    assert selected["arguments"]["parameters"]["code"] == "10080022"
    assert selected["arguments"]["parameters"]["page"] == 2
    assert selected["arguments"]["parameters"]["page_size"] == 200
    assert repo.lookup_calls == 1
    assert repo.candidate_calls == 0
