"""Facade de domain para LLM na descoberta de rótulos de coluna."""

from __future__ import annotations

from typing import ClassVar

from app.domain.ports.llm_gateway_port import LlmGatewayPort


class PresentationColumnLabelLlmService:
    _gateway: ClassVar[LlmGatewayPort | None] = None

    @classmethod
    def configure(cls, gateway: LlmGatewayPort) -> None:
        cls._gateway = gateway

    @classmethod
    def generate(cls, messages: list[dict[str, str]]) -> str:
        if cls._gateway is None:
            return ""

        try:
            return str(cls._gateway.generate(messages) or "")
        except Exception:
            return ""
