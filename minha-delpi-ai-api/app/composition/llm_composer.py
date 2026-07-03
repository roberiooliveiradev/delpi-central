from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.composition.provider_registry import resolve_llm_gateway_factory


def make_llm_gateway() -> LlmGatewayPort:
    return resolve_llm_gateway_factory()()
