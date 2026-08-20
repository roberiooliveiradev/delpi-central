from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.infrastructure.config.llm_text_config import resolve_llm_text_config
from app.infrastructure.llm.llm_request_context import get_active_config, get_active_llm_provider


class ChatLlmMetadataService:
    @staticmethod
    def resolve_generation_config(request: SendChatMessageRequest):
        return ChatResponseModeService.resolve(request.response_mode)

    @staticmethod
    def build_runtime_snapshot() -> dict[str, object]:
        """Provider/modelo ativos do turno — fonte única para metadata e adminDebug."""
        active = get_active_config()
        text = resolve_llm_text_config()
        provider = get_active_llm_provider()

        return {
            "provider": provider,
            "model": active.model,
            "responseMode": active.response_mode,
            "baseUrl": text.base_url,
            "configuredProvider": text.provider,
            "configuredModel": text.model,
            "maxTokens": active.max_tokens,
            "numCtx": active.num_ctx,
            "temperature": active.temperature,
            "costRates": ChatLlmMetadataService._resolve_cost_rates(
                provider=provider,
                model=str(active.model or ""),
            ),
        }

    @staticmethod
    def _resolve_cost_rates(*, provider: str, model: str) -> dict[str, object]:
        try:
            from app.application.services.llm_cost_estimator_service import (
                LlmCostEstimatorService,
            )

            rates = LlmCostEstimatorService().resolve_rates(provider=provider, model=model)
            return {
                "promptCostPer1k": rates.get("promptCostPer1k"),
                "completionCostPer1k": rates.get("completionCostPer1k"),
                "currency": rates.get("currency") or "BRL",
                "source": rates.get("source") or "env_default",
            }
        except Exception:
            return {
                "promptCostPer1k": None,
                "completionCostPer1k": None,
                "currency": "BRL",
                "source": "unavailable",
            }

    @staticmethod
    def build_assistant_llm_fields() -> dict[str, object]:
        snapshot = ChatLlmMetadataService.build_runtime_snapshot()

        return {
            "provider": snapshot["provider"],
            "model": snapshot["model"],
            "responseMode": snapshot["responseMode"],
            "llm": {
                "provider": snapshot["provider"],
                "model": snapshot["model"],
                "responseMode": snapshot["responseMode"],
                "baseUrl": snapshot["baseUrl"],
                "configuredProvider": snapshot["configuredProvider"],
                "configuredModel": snapshot["configuredModel"],
                "maxTokens": snapshot["maxTokens"],
                "numCtx": snapshot["numCtx"],
                "temperature": snapshot["temperature"],
                "costRates": snapshot["costRates"],
            },
        }

    @staticmethod
    def user_message_response_mode(request: SendChatMessageRequest) -> dict[str, str]:
        mode = ChatResponseModeService.normalize(request.response_mode)

        return {"responseMode": mode}

    @staticmethod
    def user_message_typing_correction(request: SendChatMessageRequest) -> dict[str, object]:
        if not request.typing_correction:
            return {}

        return {"typingCorrection": request.typing_correction}
