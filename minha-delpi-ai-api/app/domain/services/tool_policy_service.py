from app.domain.exceptions.tool_exceptions import ToolPermissionDeniedError


class ToolPolicyService:
    def can_execute(
        self,
        tool_name: str,
        required_permission: str,
        permission_context: dict,
    ) -> bool:
        if permission_context.get("is_superadmin"):
            return True

        permissions = permission_context.get("permissions") or set()

        return required_permission in permissions

    def require_tool_permission(
        self,
        tool_name: str,
        required_permission: str,
        permission_context: dict,
    ) -> None:
        if not self.can_execute(
            tool_name=tool_name,
            required_permission=required_permission,
            permission_context=permission_context,
        ):
            raise ToolPermissionDeniedError(
                tool_name=tool_name,
                permission=required_permission,
            )

    def sanitize_for_llm(self, data):
        if isinstance(data, dict):
            return {
                key: self.sanitize_for_llm(value)
                for key, value in data.items()
                if key not in {"access_token", "refresh_token", "token", "client_secret"}
            }

        if isinstance(data, list):
            return [self.sanitize_for_llm(item) for item in data]

        return data
