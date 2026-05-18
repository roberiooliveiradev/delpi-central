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

        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]

        if not paragraphs:
            yield text
            return

        for index, paragraph in enumerate(paragraphs):
            if index > 0:
                yield "\n\n"

            yield paragraph
