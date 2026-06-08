from app.application.services.external_actions.external_action_sql_route_selection_service import (
    ExternalActionSqlRouteSelectionService,
)


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions

    def list_actions(self):
        return list(self._actions)

    def find_candidate_actions(self, message, limit=120, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        matches = list(self._actions)[:limit]

        if allowed:
            matches = [
                action
                for action in matches
                if str(action.get("actionId")) in allowed
            ]

        return matches


def test_select_sql_uses_data_sql_action_when_sql_provided():
    repository = _FakeRepository(
        [
            {
                "actionId": "sql-action",
                "method": "POST",
                "path": "/data/sql",
                "operationId": "execute_sql",
                "parametersSchema": [],
            },
            {
                "actionId": "kpi-action",
                "method": "GET",
                "path": "/production/kpi",
                "operationId": "get_production_kpi",
                "parametersSchema": [],
            },
        ]
    )
    service = ExternalActionSqlRouteSelectionService(repository)

    selected = service.select(
        "consulta ignorada",
        ["sql-action", "kpi-action"],
        sql="SELECT A1_COD FROM SA1010",
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "sql-action"
    assert "SELECT A1_COD" in selected["arguments"]["body"]["sql"]


def test_select_sql_without_embedded_query_uses_message_body():
    repository = _FakeRepository(
        [
            {
                "actionId": "sql-action",
                "method": "POST",
                "path": "/data/sql",
                "operationId": "execute_sql",
                "summary": "Executar SQL",
                "parametersSchema": [{"name": "query"}],
            },
        ]
    )
    service = ExternalActionSqlRouteSelectionService(repository)
    message = "execute essa consulta no banco"

    selected = service.select(
        message,
        ["sql-action"],
        candidates_loader=lambda _message, *, allowed_action_ids, limit: repository.list_actions(),
        rank_candidates=lambda _message, candidates, **kwargs: candidates,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "sql-action"
    assert selected["arguments"]["body"] == {"message": message}
