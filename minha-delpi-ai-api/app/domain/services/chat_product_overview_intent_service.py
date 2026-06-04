"""Perguntas abertas sobre o produto («me fale do produto X») — narrativa + insights."""

from __future__ import annotations

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatProductOverviewIntentService:
    _OVERVIEW_TERMS = (
        "me fale do produto",
        "me fale sobre o produto",
        "me fale sobre produto",
        "me fale do item",
        "me fale sobre o item",
        "me conte sobre o produto",
        "me conte do produto",
        "fale do produto",
        "fale sobre o produto",
        "fale sobre o item",
        "conte sobre o produto",
        "conte sobre o item",
        "o que voce sabe do produto",
        "o que você sabe do produto",
        "o que voce sabe sobre o produto",
        "o que você sabe sobre o produto",
        "quero saber do produto",
        "quero saber sobre o produto",
        "informacoes do produto",
        "informações do produto",
        "informacoes sobre o produto",
        "informações sobre o produto",
        "dados do produto",
        "cadastro do produto",
        "visao geral do produto",
        "visão geral do produto",
        "tudo sobre o produto",
    )

    _NARROW_TERMS = (
        "estoque",
        "estrutura",
        "bom",
        "preço",
        "preco",
        "fornecedor",
        "roteiro",
        "inspeção",
        "inspecao",
        "venda",
        "compra",
        "nota fiscal",
        "resumo de venda",
        "resumo de kaizen",
        "ficha completa",
        "analisador",
        "analyzer",
    )

    @classmethod
    def is_product_overview_message(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not ChatProductQueryIntentService.extract_product_code(message or ""):
            return False

        if any(term in normalized for term in cls._NARROW_TERMS):
            return False

        if ChatProductQueryIntentService._looks_like_stock_question(normalized):
            return False

        if ChatProductQueryIntentService._looks_like_structure_question(normalized):
            return False

        if ChatProductQueryIntentService._looks_like_sales_question(normalized):
            return False

        if ChatProductQueryIntentService._looks_like_full_analyser_question(normalized):
            return False

        if any(term in normalized for term in cls._OVERVIEW_TERMS):
            return True

        if "resumo do produto" in normalized or "resumo sintetico" in normalized:
            return True

        if re_match := cls._me_fale_with_product(normalized):
            return re_match

        return False

    @classmethod
    def _me_fale_with_product(cls, normalized: str) -> bool:
        import re

        if not re.search(r"\bme fale\b", normalized):
            return False

        return any(
            token in normalized
            for token in ("produto", "item", "material", "codigo", "código", "sku")
        )

    @classmethod
    def should_force_llm_synthesis(
        cls,
        message: str | None,
        tool_calls: list | None = None,
    ) -> bool:
        if not cls.is_product_overview_message(message):
            return False

        if not tool_calls:
            return True

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata") or {}

            if metadata.get("ok"):
                return True

        return False

    @classmethod
    def blocks_presentation_only_shortcut(cls, message: str | None) -> bool:
        return cls.is_product_overview_message(message)

    @classmethod
    def build_prompt_policy_addon(cls, message: str | None) -> str:
        if not cls.is_product_overview_message(message):
            return ""

        from app.domain.services.prompt_policy_service import PromptPolicyService

        return (
            "\n\n"
            + PromptPolicyService()._load_policy(
                "product-overview.md",
                "Modo visão do produto: narrativa com insights.",
            )
        )
