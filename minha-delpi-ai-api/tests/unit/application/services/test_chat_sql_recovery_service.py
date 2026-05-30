from dataclasses import dataclass

from app.application.services.chat_sql_recovery_service import ChatSqlRecoveryService
from app.domain.entities.tool_result import ToolResult


@dataclass
class FakeRequest:
    user_id: str
    access_token: str
    tool_name: str
    arguments: dict


class FakeRepository:
    def find_candidate_actions(self, message, limit=120, allowed_action_ids=None):
        actions = [
            {
                "actionId": "schema-action",
                "method": "GET",
                "path": "/system/tables/{tableName}/schema",
            },
            {
                "actionId": "sql-action",
                "method": "POST",
                "path": "/data/sql",
            },
        ]
        allowed = set(allowed_action_ids or [])
        return [action for action in actions if action["actionId"] in allowed]


class FakeExecuteToolUseCase:
    def __init__(self):
        self.calls: list[dict] = []

    def execute(self, request):
        self.calls.append(request.arguments)
        action_id = request.arguments.get("actionId")

        if action_id == "schema-action":
            return ToolResult(
                name="execute_external_action",
                data={
                    "columns": {
                        "results": [
                            {"X3_CAMPO": "D4_OP"},
                            {"X3_CAMPO": "D4_OPERAC"},
                        ]
                    }
                },
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/system/tables/SD4010/schema",
                    "actionId": action_id,
                },
            )

        return ToolResult(
            name="execute_external_action",
            data={"success": True, "data": [{"COD_PRODUTO": "123"}]},
            metadata={
                "ok": True,
                "statusCode": 200,
                "path": "/data/sql",
                "actionId": action_id,
            },
        )


def test_maybe_recover_fetches_schema_and_retries_sql():
    execute_tool = FakeExecuteToolUseCase()
    service = ChatSqlRecoveryService(execute_tool, FakeRepository())

    sql = "SELECT RE.D4_OPER FROM SD4010 RE"
    recovery = service.maybe_recover(
        user_id="user-1",
        access_token="token",
        allowed_action_ids=["schema-action", "sql-action"],
        arguments={"body": {"sql": sql}},
        metadata={
            "ok": False,
            "statusCode": 400,
            "path": "/data/sql",
            "responsePreview": "Invalid column name 'D4_OPER'.",
        },
    )

    assert recovery is not None
    assert recovery.plan.replacement_column == "D4_OPERAC"
    assert len(execute_tool.calls) == 2
    assert execute_tool.calls[0]["actionId"] == "schema-action"
    assert execute_tool.calls[1]["body"]["sql"] == recovery.plan.corrected_sql
