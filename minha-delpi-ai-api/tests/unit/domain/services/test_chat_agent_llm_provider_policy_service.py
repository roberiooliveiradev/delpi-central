from app.domain.services.chat_agent_llm_provider_policy_service import (
    ChatAgentLlmProviderPolicyService,
)


def test_text_provider_override_reads_intelligence_metadata():
    assert ChatAgentLlmProviderPolicyService.text_provider_override(
        {
            "metadata": {
                "intelligence": {"llmProviderOverride": "openai_compatible"},
            }
        }
    ) == "openai_compatible"


def test_text_provider_override_reads_legacy_metadata_flag():
    assert ChatAgentLlmProviderPolicyService.text_provider_override(
        {"metadata": {"llmProviderOverride": "vllm"}}
    ) == "openai_compatible"


def test_text_provider_override_returns_none_without_flag():
    assert ChatAgentLlmProviderPolicyService.text_provider_override(None) is None
    assert ChatAgentLlmProviderPolicyService.text_provider_override({}) is None
    assert (
        ChatAgentLlmProviderPolicyService.text_provider_override(
            {"metadata": {"intelligence": {}}}
        )
        is None
    )
