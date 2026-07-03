from app.domain.ports.fine_tuning_model_gateway_port import FineTuningModelGatewayPort
from app.infrastructure.config.llm_text_config import resolve_llm_provider_name
from app.infrastructure.llm.export_only_fine_tuning_model_gateway import (
    ExportOnlyFineTuningModelGateway,
)
from app.infrastructure.llm.ollama_fine_tuning_model_gateway import OllamaFineTuningModelGateway


def make_fine_tuning_model_gateway() -> FineTuningModelGatewayPort:
    if resolve_llm_provider_name() == "ollama":
        return OllamaFineTuningModelGateway()

    return ExportOnlyFineTuningModelGateway()
