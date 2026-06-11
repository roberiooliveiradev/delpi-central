from app.application.services.chat_native_tool_calling_service import (
    ChatNativeToolCallingService,
)
from app.domain.entities.llm_generation_result import LlmGenerationResult, LlmToolCall
from app.domain.ports.internal_tool_port import InternalToolPort


class StubTool(InternalToolPort):
    name = "get_current_user"
    description = "Usuário atual."
    required_permission = "chat.access"

    def execute(self, arguments: dict, access_token: str):
        raise NotImplementedError


class FakeLlm:
    def supports_native_tools(self) -> bool:
        return True

    def generate_with_tools(self, messages, tools):
        return LlmGenerationResult(
            content="",
            tool_calls=[
                LlmToolCall(id="1", name="get_current_user", arguments={}),
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
