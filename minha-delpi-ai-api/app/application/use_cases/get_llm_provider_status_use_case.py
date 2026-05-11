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
        }
