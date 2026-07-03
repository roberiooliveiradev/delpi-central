from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.llm.context_aware_llm_gateway import ContextAwareLlmGateway


def make_llm_gateway() -> LlmGatewayPort:
    return ContextAwareLlmGateway()
