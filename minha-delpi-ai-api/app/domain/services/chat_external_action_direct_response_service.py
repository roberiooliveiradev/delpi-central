import re
import time

from app.infrastructure.config.settings import Settings


class ChatExternalActionDirectResponseService:
    @staticmethod
    def is_enabled() -> bool:
        return Settings.CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED

    @staticmethod
    def should_skip_rag(tool_context: dict | None) -> bool:
        if not tool_context:
            return False

        if tool_context.get("skipRag"):
            return True

        return bool(tool_context.get("directAnswer"))

    @staticmethod
    def resolve_answer(tool_context: dict | None) -> str | None:
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

    @staticmethod
    def iter_stream_chunks(answer: str):
        text = answer.strip()

        if not text:
            return

        chunk_size = max(1, Settings.CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS)
        delay_seconds = max(0.0, Settings.CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS) / 1000.0

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
