from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.entities.tool_result import ToolResult
from app.domain.exceptions.tool_exceptions import InvalidToolInputError
from app.domain.ports.internal_tool_port import InternalToolPort


class ExecuteExternalActionTool(InternalToolPort):
    name = "execute_external_action"
    description = "Executa uma action HTTP importada de um schema OpenAPI cadastrado no Minha DELPI Chat."
    required_permission = "minha-delpi.chat.tools.use"

    def __init__(self, use_case: ExecuteExternalActionUseCase):
        self.use_case = use_case

    def execute(self, arguments: dict, access_token: str) -> ToolResult:
        action_id = str(arguments.get("actionId") or "").strip()

        if not action_id:
            raise InvalidToolInputError("actionId is required")

        user_id = str(arguments.get("_userId") or "").strip()

        if not user_id:
            raise InvalidToolInputError("_userId is required")

        action_arguments = {
            "parameters": arguments.get("parameters") or {},
            "body": arguments.get("body"),
        }

        try:
            result = self.use_case.execute(
                user_id=user_id,
                access_token=access_token,
                action_id=action_id,
                arguments=action_arguments,
            )
        except ValueError as exc:
            raise InvalidToolInputError(str(exc)) from exc

        return ToolResult(
            name=self.name,
            data=result["data"],
            metadata={
                "provider": result["provider"],
                "actionId": result["actionId"],
                "method": result["method"],
                "path": result["path"],
                "statusCode": result["statusCode"],
                "ok": result["ok"],
                **result["metadata"],
            },
        )
