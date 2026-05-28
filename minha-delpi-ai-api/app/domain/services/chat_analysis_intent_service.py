import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatAnalysisIntentService:
    """Detecta pedidos de comparação, apontamentos e insights (sem nova consulta operacional)."""

    _COMPARISON_TERMS = (
        "compar",
        "compare",
        "versus",
        " vs ",
        "diferen",
        "diferenc",
        "insight",
        "apontament",
        "analis",
        "analise",
        "análise",
        "contrast",
        "semelhan",
        "similaridad",
        "distin",
        "lado a lado",
        "entre as duas",
        "entre os dois",
        "entre elas",
        "entre eles",
        "as duas estrutura",
        "os dois produto",
        "os dois item",
        "o que mudou",
        "o que difere",
        "quais difer",
        "traga insight",
        "trazer insight",
        "pontos em comum",
        "em comum e",
    )

    _STRUCTURE_PATH_RE = re.compile(
        r"/products/(?P<code>[^/]+)/structure",
        re.IGNORECASE,
    )

    @classmethod
    def is_comparison_or_insight_request(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(term in normalized for term in cls._COMPARISON_TERMS):
            return True

        if ("as duas" in normalized or "os dois" in normalized or "ambos" in normalized) and any(
            token in normalized
            for token in (
                "estrutura",
                "produto",
                "item",
                "bom",
                "consulta",
                "resultado",
            )
        ):
            return True

        return False

    @classmethod
    def extract_all_product_codes(cls, *texts: str | None) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []

        for text in texts:
            if not text:
                continue

            raw = str(text)

            for match in ChatProductQueryIntentService._PRODUCT_CODE_RE.finditer(raw):
                if ChatProductQueryIntentService._is_group_code_numeric_token(raw, match):
                    continue

                code = ChatProductQueryIntentService.normalize_product_code(match.group(0))

                if not code or code in seen:
                    continue

                seen.add(code)
                ordered.append(code)

        return ordered

    @classmethod
    def extract_product_codes_for_action_planning(
        cls,
        message: str,
        conversation_context: str | None = None,
    ) -> list[str]:
        """Códigos para planejar consultas paralelas à API.

        Se a mensagem atual já traz código(s), não puxa códigos extras do histórico
        (evita N× estoque quando o usuário pergunta só de um produto).
        """
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        codes_in_message = cls.extract_all_product_codes(message)

        if codes_in_message:
            return codes_in_message

        if ChatProductQueryIntentService.references_previous_product(message):
            code = ChatProductQueryIntentService.resolve_product_code(
                message,
                conversation_context,
            )

            return [code] if code else []

        return []

    @classmethod
    def extract_product_code_from_tool_path(cls, path: str | None) -> str | None:
        if not path:
            return None

        match = cls._STRUCTURE_PATH_RE.search(str(path))

        if not match:
            return None

        return ChatProductQueryIntentService.normalize_product_code(match.group("code"))
