"""Normalização de nomes de provedor LLM (playbook 24 — lógica pura de domínio)."""

from __future__ import annotations

OPENAI_COMPATIBLE_PROVIDERS = frozenset({"vllm", "openai_compatible", "openai"})

# Stack padrão da plataforma: LLM externo (Kimi/OpenRouter). Ollama só com valor explícito.
DEFAULT_LLM_PROVIDER = "openai_compatible"


class ChatLlmProviderNormalizationService:
    @staticmethod
    def normalize(provider: str) -> str:
        normalized = str(provider or "").lower().strip()
        if not normalized:
            return DEFAULT_LLM_PROVIDER

        if normalized in OPENAI_COMPATIBLE_PROVIDERS:
            return "openai_compatible"

        if normalized == "ollama":
            return "ollama"

        # Desconhecido: não coerir para ollama — registry falha de forma explícita.
        return normalized

    @staticmethod
    def is_openai_compatible(provider: str) -> bool:
        return ChatLlmProviderNormalizationService.normalize(provider) == "openai_compatible"
