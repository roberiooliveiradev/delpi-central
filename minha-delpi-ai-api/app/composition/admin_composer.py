from app.application.use_cases.get_llm_provider_status_use_case import (
    GetLlmProviderStatusUseCase,
)


def make_get_llm_provider_status_use_case() -> GetLlmProviderStatusUseCase:
    return GetLlmProviderStatusUseCase()
