"""Resolução canônica de configuração LLM no domain (via AppConfigPort)."""

from __future__ import annotations

from app.domain.entities.llm_text_config import LlmTextConfig
from app.domain.services.chat_domain_config_service import ChatDomainConfigService


class LlmProviderConfigService:
    @classmethod
    def resolve_text_config(cls) -> LlmTextConfig:
        provider = ChatDomainConfigService.llm_provider()
        model = ChatDomainConfigService.llm_text_model()
        base_url = ChatDomainConfigService.llm_text_base_url().rstrip("/")
        api_key = ChatDomainConfigService.llm_text_api_key()
        timeout = ChatDomainConfigService.llm_text_timeout_seconds()

        return LlmTextConfig(
            provider=provider,
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout_seconds=timeout,
        )

    @classmethod
    def embedding_provider(cls) -> str:
        return ChatDomainConfigService.embedding_provider()

    @classmethod
    def embedding_model(cls) -> str:
        return ChatDomainConfigService.embedding_model()

    @classmethod
    def embedding_base_url(cls) -> str:
        return ChatDomainConfigService.embedding_base_url().rstrip("/")

    @classmethod
    def vision_llm_provider(cls) -> str:
        return ChatDomainConfigService.vision_llm_provider()

    @classmethod
    def vision_llm_model(cls) -> str:
        return ChatDomainConfigService.vision_llm_model()
