from app.application.services.chat_native_tool_schema_service import (
    ChatNativeToolSchemaService,
)
from app.domain.ports.internal_tool_port import InternalToolPort


class StubTool(InternalToolPort):
    name = "get_current_user"
    description = "Usuário atual."
    required_permission = "chat.access"

    def execute(self, arguments: dict, access_token: str):
        raise NotImplementedError


def test_build_openai_tools_excludes_execute_external_action():
    service = ChatNativeToolSchemaService()
    registry = {
        "get_current_user": StubTool(),
        "execute_external_action": StubTool(),
    }
    registry["execute_external_action"].name = "execute_external_action"

    schemas = service.build_openai_tools(
        allowed_tool_names=["get_current_user", "execute_external_action"],
        tools_registry=registry,
    )

    names = [item["function"]["name"] for item in schemas]

    assert names == ["get_current_user"]
