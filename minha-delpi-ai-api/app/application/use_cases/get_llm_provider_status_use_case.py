from app.infrastructure.config.llm_latency_profile import describe_active_profile
from app.infrastructure.config.settings import Settings


class GetLlmProviderStatusUseCase:
    def execute(self) -> dict:
        model = Settings.OLLAMA_MODEL

        if Settings.LLM_PROVIDER == "vllm":
            model = Settings.VLLM_MODEL

        return {
            "provider": Settings.LLM_PROVIDER,
            "model": model,
            "temperature": Settings.LLM_TEMPERATURE,
            "maxTokens": Settings.LLM_MAX_TOKENS,
            "latencyProfile": describe_active_profile(),
        }
