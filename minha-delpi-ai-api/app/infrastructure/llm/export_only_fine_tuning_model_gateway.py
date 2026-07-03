from __future__ import annotations

from app.domain.ports.fine_tuning_model_gateway_port import FineTuningModelGatewayPort
from app.domain.services.chat_learning_content_service import ChatLearningContentService
from app.infrastructure.config.llm_text_config import resolve_llm_provider_name


class ExportOnlyFineTuningModelGateway(FineTuningModelGatewayPort):
    def supports_local_deploy(self) -> bool:
        return False

    def provider_name(self) -> str:
        return resolve_llm_provider_name()

    def create_from_modelfile(self, *, name: str, modelfile: str) -> dict:
        raise RuntimeError(
            ChatLearningContentService.get(
                "fineTuning",
                "localDeployUnavailable",
                default="Deploy local de fine-tuning indisponível para o provedor LLM atual.",
            )
        )
