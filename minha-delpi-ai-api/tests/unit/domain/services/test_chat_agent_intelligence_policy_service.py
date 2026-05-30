from app.domain.services.chat_agent_intelligence_policy_service import (
    ChatAgentIntelligencePolicyService,
)


def test_native_tool_calling_requires_agent_intelligence_flag():
    assert not ChatAgentIntelligencePolicyService.native_tool_calling_pilot_enabled(None)
    assert not ChatAgentIntelligencePolicyService.native_tool_calling_pilot_enabled({})
    assert not ChatAgentIntelligencePolicyService.native_tool_calling_pilot_enabled(
        {"metadata": {}}
    )
    assert ChatAgentIntelligencePolicyService.native_tool_calling_pilot_enabled(
        {"metadata": {"intelligence": {"nativeToolCallingEnabled": True}}}
    )


def test_native_tool_calling_legacy_metadata_flag():
    assert ChatAgentIntelligencePolicyService.native_tool_calling_pilot_enabled(
        {"metadata": {"nativeToolCallingEnabled": True}}
    )
