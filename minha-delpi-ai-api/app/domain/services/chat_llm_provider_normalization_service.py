"""Normalização de nomes de provedor LLM (playbook 24 — lógica pura de domínio)."""

from __future__ import annotations

OPENAI_COMPATIBLE_PROVIDERS = frozenset({"vllm", "openai_compatible", "openai"})


class ChatLlmProviderNormalizationService:
    @staticmethod
    def normalize(provider: str) -> str:
        normalized = str(provider or "ollama").lower().strip()

        if normalized in OPENAI_COMPATIBLE_PROVIDERS:
            return "openai_compatible"

        return normalized

    @staticmethod
    def is_openai_compatible(provider: str) -> bool:
        return ChatLlmProviderNormalizationService.normalize(provider) == "openai_compatible"
