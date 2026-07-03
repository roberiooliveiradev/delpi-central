"""Gateway LLM que delega ao provider ativo no contexto da requisição."""

from __future__ import annotations

from collections.abc import Iterator

from app.domain.entities.llm_generation_result import LlmGenerationResult
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_llm_generation_context_service import get_active_llm_provider
from app.infrastructure.llm.llm_gateway_registry import get_gateway_for_provider


class ContextAwareLlmGateway(LlmGatewayPort):
    def _delegate(self) -> LlmGatewayPort:
        return get_gateway_for_provider(get_active_llm_provider())

    def supports_native_tools(self) -> bool:
        return self._delegate().supports_native_tools()

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> LlmGenerationResult:
        return self._delegate().generate_with_tools(messages, tools)

    def generate(self, messages: list[dict]) -> str:
        return self._delegate().generate(messages)

    def stream(self, messages: list[dict]) -> Iterator[str]:
        return self._delegate().stream(messages)
