from app.application.services.chat_native_tool_calling_service import (
    ChatNativeToolCallingService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.entities.llm_generation_result import LlmGenerationResult, LlmToolCall
from app.domain.ports.internal_tool_port import InternalToolPort

configure_domain_infrastructure_ports()


class StubTool(InternalToolPort):
    name = "get_current_user"
    description = "Usuário atual."
    required_permission = "chat.access"

    def execute(self, arguments: dict, access_token: str):
        raise NotImplementedError


class StubSearchTool(InternalToolPort):
    name = "search_knowledge_base"
    description = "Busca."
    required_permission = "chat.access"

    def execute(self, arguments: dict, access_token: str):
        raise NotImplementedError


class FakeLlm:
    def __init__(self, tool_names: list[str] | None = None):
        self.tool_names = tool_names or ["get_current_user"]
        self.last_tools = None

    def supports_native_tools(self) -> bool:
        return True

    def generate_with_tools(self, messages, tools):
        self.last_tools = tools
        return LlmGenerationResult(
            content="",
            tool_calls=[
                LlmToolCall(id=str(index), name=name, arguments={})
                for index, name in enumerate(self.tool_names, start=1)
            ],
        )


class FakeSettingsRepository:
    def get_chat_intelligence_settings(self):
        return {"nativeToolCallingEnabled": True}

    def save_chat_intelligence_settings(self, payload):
        pass


class FakeIntelligenceSettingsService:
    def __init__(self, *, native_tool_calling_enabled: bool = True):
        self.settings_repository = FakeSettingsRepository()
        self._native_tool_calling_enabled = native_tool_calling_enabled

    def resolve(self):
        from types import SimpleNamespace

        return SimpleNamespace(
            native_tool_calling_enabled=self._native_tool_calling_enabled,
        )


def test_select_tools_when_enabled():
    service = ChatNativeToolCallingService(
        llm_gateway=FakeLlm(),
        intelligence_settings_service=FakeIntelligenceSettingsService(
            native_tool_calling_enabled=True,
        ),
    )

    pilot_agent = {"metadata": {"intelligence": {"nativeToolCallingEnabled": True}}}

    result = service.select_tools(
        message="quem sou eu?",
        allowed_tool_names=["get_current_user"],
        tools_registry={"get_current_user": StubTool()},
        agent_context=pilot_agent,
    )

    assert result["meta"]["used"] is True
    assert result["meta"]["pilotAgentEnabled"] is True
    assert result["meta"]["providerSupports"] is True
    assert result["meta"]["shortlistSize"] == 1
    assert result["selections"][0]["name"] == "get_current_user"


def test_select_tools_blocked_without_pilot_agent():
    service = ChatNativeToolCallingService(
        llm_gateway=FakeLlm(),
        intelligence_settings_service=FakeIntelligenceSettingsService(
            native_tool_calling_enabled=True,
        ),
    )

    result = service.select_tools(
        message="quem sou eu?",
        allowed_tool_names=["get_current_user"],
        tools_registry={"get_current_user": StubTool()},
        agent_context={"metadata": {}},
    )

    assert result["meta"]["used"] is False
    assert result["meta"]["pilotAgentEnabled"] is False
    assert result["selections"] == []


def test_select_tools_respects_shortlist_and_max_tool_calls():
    llm = FakeLlm(tool_names=["get_current_user", "search_knowledge_base"])
    service = ChatNativeToolCallingService(
        llm_gateway=llm,
        intelligence_settings_service=FakeIntelligenceSettingsService(
            native_tool_calling_enabled=True,
        ),
    )
    pilot_agent = {
        "metadata": {"intelligence": {"nativeToolCallingEnabled": True}},
        "maxToolCalls": 1,
    }

    result = service.select_tools(
        message="quem sou eu e busque na base?",
        allowed_tool_names=["get_current_user", "search_knowledge_base", "web_search"],
        tools_registry={
            "get_current_user": StubTool(),
            "search_knowledge_base": StubSearchTool(),
        },
        agent_context=pilot_agent,
        shortlist_tool_names=["get_current_user", "search_knowledge_base"],
        max_tool_calls=1,
    )

    assert result["meta"]["maxToolCalls"] == 1
    assert result["meta"]["shortlistSize"] == 2
    assert len(result["selections"]) == 1
    assert result["meta"]["truncated"] is True
    assert isinstance(llm.last_tools, list)
    assert len(llm.last_tools) == 2
