class LlmProviderError(Exception):
    code = "llm.provider_error"
    message = "LLM provider error"


class LlmProviderUnavailableError(LlmProviderError):
    code = "llm.unavailable"
    message = "LLM provider unavailable"
