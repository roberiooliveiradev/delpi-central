"""Override de provedor LLM por agente (playbook 24 — P5)."""

from __future__ import annotations

from app.domain.services.chat_agent_intelligence_policy_service import (
    ChatAgentIntelligencePolicyService,
)
from app.domain.services.chat_llm_provider_normalization_service import (
    ChatLlmProviderNormalizationService,
)


class ChatAgentLlmProviderPolicyService:
    @classmethod
    def text_provider_override(cls, agent_context: dict | None) -> str | None:
        metadata = ChatAgentIntelligencePolicyService.agent_metadata(agent_context)
        intelligence = metadata.get("intelligence")
        raw = None

        if isinstance(intelligence, dict) and "llmProviderOverride" in intelligence:
            raw = intelligence.get("llmProviderOverride")
        elif "llmProviderOverride" in metadata:
            raw = metadata.get("llmProviderOverride")

        if raw is None:
            return None

        normalized = str(raw).strip()

        if not normalized:
            return None

        return ChatLlmProviderNormalizationService.normalize(normalized)
