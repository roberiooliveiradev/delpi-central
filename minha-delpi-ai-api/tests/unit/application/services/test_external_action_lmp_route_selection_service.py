from app.application.services.external_actions.external_action_lmp_route_selection_service import (
    ExternalActionLmpRouteSelectionService,
)


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions


def test_select_lmp_prefers_detail_route_for_sale_number():
    actions = [
        {
            "actionId": "list-lmps",
            "method": "GET",
            "path": "/engineering/lmps",
            "operationId": "list_lmps",
            "parametersSchema": [{"name": "page"}, {"name": "page_size"}],
        },
        {
            "actionId": "lmp-detail",
            "method": "GET",
            "path": "/engineering/lmps/{sale_number}",
            "operationId": "get_lmp_by_sale_number",
            "parametersSchema": [{"name": "sale_number", "in": "path", "required": True}],
        },
    ]
    service = ExternalActionLmpRouteSelectionService(_FakeRepository(actions))

    def loader(message, *, allowed_action_ids, limit):
        allowed = {str(item) for item in allowed_action_ids}
        return [action for action in actions if str(action.get("actionId")) in allowed]

    selected = service.select(
        "detalhe da LMP OV 123456",
        ["list-lmps", "lmp-detail"],
        candidates_loader=loader,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "lmp-detail"
    assert selected["arguments"]["parameters"]["sale_number"] == "123456"
