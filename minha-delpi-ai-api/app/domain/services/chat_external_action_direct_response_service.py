import re
import time
from typing import ClassVar

from app.domain.ports.app_config_port import AppConfigPort


class ChatExternalActionDirectResponseService:
    _config: ClassVar[AppConfigPort | None] = None

    @classmethod
    def configure(cls, config: AppConfigPort) -> None:
        cls._config = config

    @classmethod
    def _require_config(cls) -> AppConfigPort:
        if cls._config is None:
            raise RuntimeError(
                "AppConfigPort não configurado — chame configure_domain_infrastructure_ports()"
            )

        return cls._config

    @classmethod
    def is_enabled(cls) -> bool:
        return cls._require_config().chat_external_action_direct_response_enabled()

    @classmethod
    def should_skip_rag(cls, tool_context: dict | None) -> bool:
        if not tool_context:
            return False

        if tool_context.get("skipRag"):
            return True

        return bool(tool_context.get("directAnswer"))

    @classmethod
    def resolve_answer(cls, tool_context: dict | None) -> str | None:
        if not tool_context or not ChatExternalActionDirectResponseService.is_enabled():
            return None

        direct_answer = tool_context.get("directAnswer")

        if not isinstance(direct_answer, str):
            return None

        normalized = direct_answer.strip()

        return normalized or None

    @staticmethod
    def _iter_char_chunks(text: str, chunk_size: int):
        for index in range(0, len(text), chunk_size):
            yield text[index : index + chunk_size]

    @staticmethod
    def _iter_word_chunks(text: str, target_chars: int):
        parts = re.findall(r"\S+\s*|\s+", text)
        buffer = ""

        for part in parts:
            if not part:
                continue

            if len(buffer) + len(part) <= target_chars or not buffer.strip():
                buffer += part
                continue

            yield buffer
            buffer = part

        if buffer:
            yield buffer

    @classmethod
    def iter_stream_chunks(cls, answer: str):
        text = answer.strip()

        if not text:
            return

        config = cls._require_config()
        chunk_size = max(1, config.chat_direct_response_stream_chunk_chars())
        delay_seconds = max(0.0, config.chat_direct_response_stream_delay_ms()) / 1000.0

        use_words = len(text) >= 120 and chunk_size >= 8
        chunks = (
            ChatExternalActionDirectResponseService._iter_word_chunks(text, chunk_size)
            if use_words
            else ChatExternalActionDirectResponseService._iter_char_chunks(text, chunk_size)
        )

        for index, chunk in enumerate(chunks):
            if index > 0 and delay_seconds > 0:
                time.sleep(delay_seconds)

            yield chunk
