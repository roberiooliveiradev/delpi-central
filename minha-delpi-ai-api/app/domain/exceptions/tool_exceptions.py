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
        self.message = f"Missing permission '{permission}' for tool '{tool_name}'"
        super().__init__(self.message)


class InvalidToolInputError(ToolError):
    code = "tool.invalid_input"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
