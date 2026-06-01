"""Resolve modos de resposta do chat (rápida / normal / pensador) em configuração LLM."""

from __future__ import annotations

import os

from app.domain.entities.llm_generation_config import LlmGenerationConfig
from app.infrastructure.config.settings import Settings

VALID_MODES = frozenset({"fast", "normal", "thinker"})
DEFAULT_MODE = "normal"


class ChatResponseModeService:
    @staticmethod
    def is_enabled() -> bool:
        return os.getenv("CHAT_RESPONSE_MODES_ENABLED", "true").lower() == "true"

    @staticmethod
    def normalize(mode: str | None) -> str:
        raw = str(mode or "").strip().lower()

        aliases = {
            "rapida": "fast",
            "rápida": "fast",
            "quick": "fast",
            "veloz": "fast",
            "pensador": "thinker",
            "pensar": "thinker",
            "think": "thinker",
            "deep": "thinker",
            "profundo": "thinker",
            "balanced": "normal",
            "padrao": "normal",
            "padrão": "normal",
            "default": "normal",
        }

        resolved = aliases.get(raw, raw)

        if resolved not in VALID_MODES:
            return DEFAULT_MODE

        return resolved

    @classmethod
    def resolve(cls, mode: str | None) -> LlmGenerationConfig:
        if not cls.is_enabled():
            return cls._default_config(DEFAULT_MODE)

        normalized = cls.normalize(mode)

        if normalized == "fast":
            return cls._fast_config()

        if normalized == "thinker":
            return cls._thinker_config()

        return cls._default_config("normal")

    @classmethod
    def list_modes(cls) -> list[dict[str, object]]:
        if not cls.is_enabled():
            return []

        items = [
            {
                "id": "fast",
                "label": "Rápida",
                "description": "Respostas mais curtas e ágeis.",
                "default": False,
            },
            {
                "id": "normal",
                "label": "Normal",
                "description": "Equilíbrio entre qualidade e velocidade.",
                "default": True,
            },
            {
                "id": "thinker",
                "label": "Pensador",
                "description": "Respostas mais elaboradas (pode demorar mais).",
                "default": False,
            },
        ]

        for item in items:
            config = cls.resolve(str(item["id"]))
            item["model"] = config.model
            item["maxTokens"] = config.max_tokens
            item["numCtx"] = config.num_ctx

        return items

    @classmethod
    def _provider_default_model(cls) -> str:
        if Settings.LLM_PROVIDER == "vllm":
            return Settings.VLLM_MODEL

        return Settings.OLLAMA_MODEL

    @classmethod
    def _env_model(cls, key: str, fallback: str | None = None) -> str:
        value = os.getenv(key, "").strip()

        if value:
            return value

        if fallback:
            return fallback

        return cls._provider_default_model()

    @classmethod
    def _fast_config(cls) -> LlmGenerationConfig:
        fast_model = os.getenv("CHAT_RESPONSE_MODE_FAST_MODEL", "qwen2.5:1.5b").strip()

        return LlmGenerationConfig(
            model=fast_model or "qwen2.5:1.5b",
            max_tokens=int(os.getenv("CHAT_RESPONSE_MODE_FAST_MAX_TOKENS", "384")),
            num_ctx=int(os.getenv("CHAT_RESPONSE_MODE_FAST_NUM_CTX", "1536")),
            temperature=float(os.getenv("CHAT_RESPONSE_MODE_FAST_TEMPERATURE", "0.3")),
            response_mode="fast",
        )

    @classmethod
    def _thinker_config(cls) -> LlmGenerationConfig:
        return LlmGenerationConfig(
            model=cls._env_model("CHAT_RESPONSE_MODE_THINKER_MODEL"),
            max_tokens=int(
                os.getenv(
                    "CHAT_RESPONSE_MODE_THINKER_MAX_TOKENS",
                    str(max(Settings.LLM_MAX_TOKENS, 1536)),
                )
            ),
            num_ctx=int(os.getenv("CHAT_RESPONSE_MODE_THINKER_NUM_CTX", "4096")),
            temperature=float(os.getenv("CHAT_RESPONSE_MODE_THINKER_TEMPERATURE", "0.25")),
            response_mode="thinker",
        )

    @classmethod
    def _default_config(cls, response_mode: str) -> LlmGenerationConfig:
        return LlmGenerationConfig(
            model=cls._provider_default_model(),
            max_tokens=Settings.LLM_MAX_TOKENS,
            num_ctx=Settings.OLLAMA_NUM_CTX,
            temperature=Settings.LLM_TEMPERATURE,
            response_mode=response_mode,
        )
