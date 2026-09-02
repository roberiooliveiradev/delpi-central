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


def test_select_sql_without_executable_query_returns_none():
    """Sem SELECT…FROM não ranquear REST (ex.: schedule/today) nem body só com message."""
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
            {
                "actionId": "schedule-action",
                "method": "GET",
                "path": "/production/schedule/today",
                "operationId": "get_production_schedule_today",
                "summary": "Produtos programados hoje",
                "parametersSchema": [],
            },
        ]
    )
    service = ExternalActionSqlRouteSelectionService(repository)
    message = (
        "executa no banco esse select top 10 de produtos do grupo 1008 "
        "(SB1010, B1_COD, B1_DESC, B1_GRUPO)"
    )

    selected = service.select(
        message,
        ["sql-action", "schedule-action"],
        candidates_loader=lambda _message, *, allowed_action_ids, limit: repository.list_actions(),
        rank_candidates=lambda _message, candidates, **kwargs: candidates,
    )

    assert selected is None


def test_select_sql_with_embedded_select_from_uses_sql_action_only():
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
            {
                "actionId": "schedule-action",
                "method": "GET",
                "path": "/production/schedule/today",
                "operationId": "get_production_schedule_today",
                "summary": "Produtos programados hoje",
                "parametersSchema": [],
            },
        ]
    )
    service = ExternalActionSqlRouteSelectionService(repository)
    message = (
        'execute: SELECT TOP 10 B1_COD FROM SB1010 WHERE B1_GRUPO = \'1008\''
    )

    selected = service.select(
        message,
        ["sql-action", "schedule-action"],
        candidates_loader=lambda _message, *, allowed_action_ids, limit: repository.list_actions(),
        rank_candidates=lambda _message, candidates, **kwargs: list(reversed(candidates)),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "sql-action"
    assert "SB1010" in selected["arguments"]["body"]["sql"].upper()
