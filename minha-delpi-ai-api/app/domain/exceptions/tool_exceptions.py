from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ToolError(Exception):
    code = "tool.error"
    message = "Tool error"


class ToolNotFoundError(ToolError):
    code = "tool.not_found"

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.message = f"Tool not found: {tool_name}"
        super().__init__(self.message)


class ToolPermissionDeniedError(ToolError):
    code = "tool.permission_denied"

    def __init__(self, tool_name: str, permission: str):
        self.tool_name = tool_name
        self.permission = permission
        self.message = ExternalActionResponseContentService.get(
            "security",
            "actionNotPermitted",
            default="Essa consulta não está liberada para este agente ou perfil.",
        )
        super().__init__(self.message)


class InvalidToolInputError(ToolError):
    code = "tool.invalid_input"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
