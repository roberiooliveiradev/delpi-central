from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_production_query_service import (
    ChatSqlProductionQueryService,
)
from app.domain.services.chat_technical_description_intent_service import (
    ChatTechnicalDescriptionIntentService,
)
from app.infrastructure.config.settings import Settings


class ChatOperationalPipelineService:
    _OPERATIONAL_TERMS = (
        "produto",
        "product",
        "item",
        "codigo",
        "código",
        "referencia",
        "referência",
        "ref ",
        " sku",
        "estoque",
        "stock",
        "saldo",
        "lmp",
        "lmps",
        "lista de materiais",
        "lista material",
        "amostra",
        "ordem de venda",
        "sql",
        "analisador",
        "analyser",
        "api delpi",
    )

    _DOCUMENTAL_TERMS = (
        "explique",
        "explica ",
        "documentação",
        "documentacao",
        "política",
        "politica",
        "procedimento",
        "como funciona",
        "o que é",
        "o que e ",
        "descreva o processo",
        "manual ",
        "norma ",
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

        if ChatSqlIntentService.is_sql_conversation_turn(message):
            if ChatSqlIntentService.is_authoring_request(message):
                return False

            if not ChatSqlIntentService.should_auto_execute_sql(message):
                return False

        if ChatAnalysisIntentService.is_comparison_or_insight_request(message):
            return False

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message):
            return False

        if ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            from app.domain.services.chat_sql_inventory_query_service import (
                ChatSqlInventoryQueryService,
            )

            return any(
                resolver.can_fast_path(message, allowed_action_ids)
                for resolver in (
                    ChatSqlProductionQueryService,
                    ChatSqlInventoryQueryService,
                )
            ) or ChatSqlIntentService.should_auto_execute_sql(message)

        if not allowed_action_ids:
            return False

        normalized = str(message or "").lower().strip()

        if not normalized:
            return False

        if cls._looks_like_documental_question(normalized) and any(
            term in normalized for term in cls._OPERATIONAL_TERMS
        ):
            return False

        if ChatProductQueryIntentService.extract_product_code(message):
            return True

        intent = ChatProductQueryIntentService.detect(message)

        if intent in (ChatProductQueryIntent.STOCK, ChatProductQueryIntent.DESCRIPTION):
            return True

        return any(term in normalized for term in cls._OPERATIONAL_TERMS)

    @classmethod
    def _looks_like_documental_question(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._DOCUMENTAL_TERMS)
