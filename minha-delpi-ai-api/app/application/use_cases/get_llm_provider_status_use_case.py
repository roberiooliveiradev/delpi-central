from app.domain.services.llm_provider_config_service import LlmProviderConfigService
from app.infrastructure.config.llm_latency_profile import describe_active_profile
from app.infrastructure.config.settings import Settings


class GetLlmProviderStatusUseCase:
    def execute(self) -> dict:
        text = LlmProviderConfigService.resolve_text_config()

        return {
            "provider": text.provider,
            "model": text.model,
            "temperature": Settings.LLM_TEMPERATURE,
            "maxTokens": Settings.LLM_MAX_TOKENS,
            "latencyProfile": describe_active_profile(),
            "text": {
                "provider": text.provider,
                "model": text.model,
                "baseUrl": text.base_url,
                "timeoutSeconds": text.timeout_seconds,
                "hasApiKey": bool(text.api_key),
            },
            "embedding": {
                "provider": LlmProviderConfigService.embedding_provider(),
                "model": LlmProviderConfigService.embedding_model(),
                "baseUrl": LlmProviderConfigService.embedding_base_url(),
            },
            "vision": {
                "provider": LlmProviderConfigService.vision_llm_provider(),
                "model": LlmProviderConfigService.vision_llm_model(),
            },
        }
