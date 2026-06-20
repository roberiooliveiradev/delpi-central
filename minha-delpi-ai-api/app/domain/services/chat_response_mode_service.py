"""Resolve modos de resposta do chat (rápida / normal / pensador) em configuração LLM."""

from __future__ import annotations

import os

from app.domain.entities.llm_generation_config import LlmGenerationConfig
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)

VALID_MODES = frozenset({"fast", "normal", "thinker"})
DEFAULT_MODE = "normal"


class ChatResponseModeService:
    @staticmethod
    def is_enabled() -> bool:
        return ChatDomainConfigService.chat_response_modes_enabled()

    @staticmethod
    def normalize(mode: str | None) -> str:
        raw = str(mode or "").strip().lower()
        aliases = ChatResponseModeContentService.alias_map()
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

        if normalized == "normal":
            return cls._normal_config()

        return cls._default_config("normal")

    @classmethod
    def list_modes(cls) -> list[dict[str, object]]:
        if not cls.is_enabled():
            return []

        items: list[dict[str, object]] = []

        for entry in ChatResponseModeContentService.mode_catalog():
            mode_id = str(entry.get("id") or "").strip()

            if mode_id not in VALID_MODES:
                continue

            item = {
                "id": mode_id,
                "label": str(entry.get("label") or mode_id),
                "description": str(entry.get("description") or ""),
                "default": bool(entry.get("default")),
            }
            config = cls.resolve(mode_id)
            item["model"] = config.model
            item["maxTokens"] = config.max_tokens
            item["numCtx"] = config.num_ctx
            items.append(item)

        if items:
            return items

        return []

    @classmethod
    def resolve_synthesis_effect(cls, response_mode: str | None) -> str:
        normalized = cls.normalize(response_mode)

        if normalized == "fast":
            return "llm_synthesis_brief"

        return "llm_synthesis"

    @classmethod
    def apply_turn_direct_answer_policy(
        cls,
        *,
        message: str,
        response_mode: str | None,
        direct_answer: str | None,
        skip_rag: bool,
        tool_calls: list | None,
    ) -> tuple[str | None, bool, str | None]:
        """Gate final: prosa narrativa via ChatPresentationProseDeliveryService (playbook-18)."""
        if not cls.is_enabled():
            return direct_answer, skip_rag, None

        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
            MODE_LLM,
        )

        mode = ChatPresentationProseDeliveryService.resolve_mode(
            message,
            tool_calls,
            response_mode=response_mode,
        )

        from app.domain.services.chat_presentation_prose_delivery_content_service import (
            ChatPresentationProseDeliveryContentService,
        )

        if (
            mode == MODE_LLM
            and direct_answer
            and not ChatPresentationProseDeliveryContentService.llm_prose_everywhere()
        ):
            return direct_answer, skip_rag, "operational_direct"

        if mode == MODE_LLM:
            effect = cls.resolve_synthesis_effect(response_mode)
            resolved_skip = cls._resolve_skip_rag_for_llm_synthesis(skip_rag, tool_calls)

            if direct_answer:
                return None, resolved_skip, effect

            return direct_answer, resolved_skip, effect

        if direct_answer:
            from app.domain.services.chat_presentation_prose_delivery_content_service import (
                ChatPresentationProseDeliveryContentService,
            )

            if ChatPresentationProseDeliveryContentService.llm_prose_everywhere():
                effect = cls.resolve_synthesis_effect(response_mode)
                resolved_skip = cls._resolve_skip_rag_for_llm_synthesis(
                    skip_rag,
                    tool_calls,
                )
                return None, resolved_skip, effect

            return direct_answer, skip_rag, "operational_direct"

        return direct_answer, skip_rag, "llm_synthesis"

    @classmethod
    def pipeline_effect_notice(cls, effect: str | None) -> str:
        if not effect:
            return ""

        return ChatResponseModeContentService.pipeline_effect_text(effect)

    @classmethod
    def _provider_default_model(cls) -> str:
        if ChatDomainConfigService.llm_provider() == "vllm":
            return ChatDomainConfigService.vllm_model()

        from app.domain.services.chat_fine_tuning_deploy_resolver_service import (
            ChatFineTuningDeployResolverService,
        )

        return ChatFineTuningDeployResolverService.resolve(
            ChatDomainConfigService.ollama_model()
        )

    @classmethod
    def _env_model(cls, key: str, fallback: str | None = None) -> str:
        value = os.getenv(key, "").strip()

        if value:
            return value

        if fallback:
            return fallback

        return cls._provider_default_model()

    @classmethod
    def _resolve_skip_rag_for_llm_synthesis(
        cls,
        skip_rag: bool,
        tool_calls: list | None,
    ) -> bool:
        """Preserva skip operacional; com tool ok os fatos já bastam — evita RAG extra no prompt."""

        if skip_rag:
            return True

        if not isinstance(tool_calls, list):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("ok"):
                return True

        return False

    @classmethod
    def _fast_config(cls) -> LlmGenerationConfig:
        fast_model = os.getenv("CHAT_RESPONSE_MODE_FAST_MODEL", "qwen2.5:1.5b").strip()

        return LlmGenerationConfig(
            model=fast_model or "qwen2.5:1.5b",
            max_tokens=int(os.getenv("CHAT_RESPONSE_MODE_FAST_MAX_TOKENS", "160")),
            num_ctx=int(os.getenv("CHAT_RESPONSE_MODE_FAST_NUM_CTX", "768")),
            temperature=float(os.getenv("CHAT_RESPONSE_MODE_FAST_TEMPERATURE", "0.2")),
            response_mode="fast",
        )

    @classmethod
    def _normal_config(cls) -> LlmGenerationConfig:
        return LlmGenerationConfig(
            model=cls._env_model("CHAT_RESPONSE_MODE_NORMAL_MODEL", "qwen2.5:1.5b"),
            max_tokens=int(os.getenv("CHAT_RESPONSE_MODE_NORMAL_MAX_TOKENS", "320")),
            num_ctx=int(os.getenv("CHAT_RESPONSE_MODE_NORMAL_NUM_CTX", "1024")),
            temperature=float(os.getenv("CHAT_RESPONSE_MODE_NORMAL_TEMPERATURE", "0.3")),
            response_mode="normal",
        )

    @classmethod
    def _thinker_config(cls) -> LlmGenerationConfig:
        return LlmGenerationConfig(
            model=cls._env_model("CHAT_RESPONSE_MODE_THINKER_MODEL", "qwen2.5:1.5b"),
            max_tokens=int(os.getenv("CHAT_RESPONSE_MODE_THINKER_MAX_TOKENS", "512")),
            num_ctx=int(os.getenv("CHAT_RESPONSE_MODE_THINKER_NUM_CTX", "1536")),
            temperature=float(os.getenv("CHAT_RESPONSE_MODE_THINKER_TEMPERATURE", "0.25")),
            response_mode="thinker",
        )

    @classmethod
    def _default_config(cls, response_mode: str) -> LlmGenerationConfig:
        return LlmGenerationConfig(
            model=cls._provider_default_model(),
            max_tokens=ChatDomainConfigService.llm_max_tokens(),
            num_ctx=ChatDomainConfigService.ollama_num_ctx(),
            temperature=ChatDomainConfigService.llm_temperature(),
            response_mode=response_mode,
        )
