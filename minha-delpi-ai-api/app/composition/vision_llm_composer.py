from app.composition.vision_llm_provider_registry import resolve_vision_llm_gateway_factory
from app.domain.ports.vision_llm_gateway_port import VisionLlmGatewayPort


def make_vision_llm_gateway() -> VisionLlmGatewayPort:
    return resolve_vision_llm_gateway_factory()()
