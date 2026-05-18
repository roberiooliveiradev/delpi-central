from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntentService
from app.infrastructure.config.settings import Settings


class ChatOperationalPipelineService:
    _OPERATIONAL_TERMS = (
        "produto",
        "product",
        "item",
        "codigo",
        "código",
        "estoque",
        "stock",
        "lmp",
        "sql",
        "analisador",
        "analyser",
    )

    @classmethod
    def is_enabled(cls) -> bool:
        return Settings.CHAT_OPERATIONAL_FAST_PATH_ENABLED

    @classmethod
    def should_optimize(
        cls,
        message: str,
        allowed_action_ids: list[str] | None,
        *,
        attachment_ids: list[str] | None = None,
    ) -> bool:
        if not cls.is_enabled():
            return False

        if attachment_ids:
            return False

        if not allowed_action_ids:
            return False

        normalized = str(message or "").lower().strip()

        if not normalized:
            return False

        if ChatProductQueryIntentService.extract_product_code(message):
            return True

        if ChatProductQueryIntentService._looks_like_stock_question(normalized):
            return True

        if ChatProductQueryIntentService._looks_like_description_question(normalized):
            return True

        return any(term in normalized for term in cls._OPERATIONAL_TERMS)
