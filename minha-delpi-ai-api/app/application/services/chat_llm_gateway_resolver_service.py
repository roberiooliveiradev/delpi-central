"""Resolve provider efetivo e gateway LLM por agente (playbook 24 — P5)."""

from __future__ import annotations

from app.domain.services.chat_agent_llm_provider_policy_service import (
    ChatAgentLlmProviderPolicyService,
)
from app.infrastructure.config.llm_text_config import resolve_llm_provider_name


class ChatLlmGatewayResolverService:
    @staticmethod
    def resolve_effective_provider(agent_context: dict | None) -> str:
        override = ChatAgentLlmProviderPolicyService.text_provider_override(agent_context)

        if override:
            return override

        return resolve_llm_provider_name()
