"""Resolve modelo LLM ativo considerando deploy de fine-tuning."""

from __future__ import annotations


class ChatFineTuningDeployResolverService:
    @classmethod
    def resolve(cls, base_model: str) -> str:
        fallback = str(base_model or "").strip()

        if not fallback:
            return fallback

        try:
            from app.infrastructure.config.settings import Settings

            if not (
                Settings.CHAT_LEARNING_ENABLED
                and Settings.CHAT_LEARNING_FINE_TUNING_ENABLED
            ):
                return fallback

            from app.composition.repository_composer import make_fine_tuning_repository

            deployed = make_fine_tuning_repository().get_active_deployed_ollama_model()

            if deployed:
                return deployed
        except Exception:
            return fallback

        return fallback
