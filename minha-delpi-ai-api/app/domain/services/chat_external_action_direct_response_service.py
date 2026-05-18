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
    def iter_stream_chunks(answer: str):
        text = answer.strip()

        if not text:
            return

        chunk_size = max(1, Settings.CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS)
        delay_seconds = max(0.0, Settings.CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS) / 1000.0

        for index in range(0, len(text), chunk_size):
            if index > 0 and delay_seconds > 0:
                time.sleep(delay_seconds)

            yield text[index : index + chunk_size]
