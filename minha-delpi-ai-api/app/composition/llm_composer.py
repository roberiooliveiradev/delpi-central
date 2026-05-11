from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.config.settings import Settings
from app.infrastructure.llm.ollama_llm_gateway import OllamaLlmGateway
from app.infrastructure.llm.vllm_llm_gateway import VllmLlmGateway


def make_llm_gateway() -> LlmGatewayPort:
    provider = Settings.LLM_PROVIDER

    if provider == "vllm":
        return VllmLlmGateway()

    if provider == "ollama":
        return OllamaLlmGateway()

    raise ValueError(f"Unsupported LLM provider: {provider}")
