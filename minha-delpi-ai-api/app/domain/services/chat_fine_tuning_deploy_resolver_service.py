"""Resolve modelo LLM ativo considerando deploy de fine-tuning."""

from __future__ import annotations


class ChatFineTuningDeployResolverService:
    @classmethod
    def resolve(cls, base_model: str) -> str:
        fallback = str(base_model or "").strip()

        if not fallback:
            return fallback

        try:
            from app.domain.services.chat_domain_config_service import ChatDomainConfigService

            if ChatDomainConfigService.llm_provider() != "ollama":
                return fallback

            if not ChatDomainConfigService.learning_pipeline_flag("learningFineTuningEnabled"):
                return fallback

            from app.composition.repository_composer import make_fine_tuning_repository

            deployed = make_fine_tuning_repository().get_active_deployed_chat_model()

            if deployed:
                return deployed
        except Exception:
            return fallback

        return fallback
