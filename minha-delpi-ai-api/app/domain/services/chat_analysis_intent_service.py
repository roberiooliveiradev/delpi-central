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
    _PRODUCT_PATH_RE = re.compile(
        r"/products/(?P<code>[^/]+)(?:/(?P<segment>[^/?]+))?",
        re.IGNORECASE,
    )
    _PATH_PLACEHOLDER_RE = re.compile(r"^\{[^}]+\}$")

    _DATA_INTERPRETATION_TERMS = (
        "explique",
        "explica ",
        "interprete",
        "interpreta",
        "o que significa",
        "o que quer dizer",
        "o que isso quer dizer",
        "me explica",
        "me explique",
        "detalhe o resultado",
        "detalhe os dados",
        "detalhe essa",
        "detalhe esta",
        "resume",
        "resuma",
        "resumir",
        "resumo do",
        "resumo da",
        "traduz",
        "traduca",
        "traduza",
        "traduzir",
        "descreva o que",
        "descrever o que",
        "em linguagem natural",
        "com palavras simples",
        "me ajude a entender",
        "ajude a entender",
        "nao entendi",
        "não entendi",
        "nao entendi o que",
        "não entendi o que",
    )

    _INTERPRETATION_SHORT_COMMANDS = (
        "resume",
        "resuma",
        "resumir",
        "traduz",
        "traduca",
        "traduza",
        "traduzir",
    )

    _DATA_REFERENCE_TERMS = (
        "dados acima",
        "resultado acima",
        "tabela acima",
        "consulta acima",
        "dados anteriores",
        "resultado anterior",
        "essa tabela",
        "esta tabela",
        "esse resultado",
        "este resultado",
        "esses dados",
        "estes dados",
        "dados mostrados",
        "dados apresentados",
        "resultado mostrado",
        "que mostrou",
        "que voce mostrou",
        "que você mostrou",
        "na tela",
        "acima",
        "anterior",
    )

    _DATA_REFERENCE_PRONOUNS = (
        "isso",
        "isto",
        "isso ai",
        "isso aí",
    )

    _EMAIL_FROM_DATA_TERMS = (
        "escreva um email",
        "escreva um e-mail",
        "escreva email",
        "escreva e-mail",
        "monte um email",
        "monte um e-mail",
        "gerar email",
        "gerar e-mail",
        "email com os dados",
        "e-mail com os dados",
        "email com a tabela",
        "e-mail com a tabela",
        "email com dados",
        "redija um email",
        "redija um e-mail",
    )

    @classmethod
    def is_email_from_operational_data_request(
        cls,
        message: str,
        previous_messages: list | None = None,
    ) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not any(term in normalized for term in cls._EMAIL_FROM_DATA_TERMS):
            return False

        return bool(
            previous_messages
            and cls._has_recent_successful_tool_data(previous_messages)
        )

    @classmethod
    def is_data_interpretation_request(
        cls,
        message: str,
        previous_messages: list | None = None,
    ) -> bool:
        """Pedido para interpretar dados já obtidos na conversa (sem nova consulta)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if cls.is_email_from_operational_data_request(message, previous_messages):
            return True

        if cls._matches_short_interpretation_command(normalized, previous_messages):
            return True

        if previous_messages and cls._has_recent_successful_tool_data(previous_messages):
            if any(
                term in normalized
                for term in (
                    "nao entendi",
                    "não entendi",
                    "nao entendi o que",
                    "não entendi o que",
                )
            ):
                return True

        if not any(term in normalized for term in cls._DATA_INTERPRETATION_TERMS):
            return False

        if any(term in normalized for term in cls._DATA_REFERENCE_TERMS):
            return bool(
                previous_messages
                and cls._has_recent_successful_tool_data(previous_messages)
            )

        if previous_messages and cls._has_recent_successful_tool_data(previous_messages):
            if any(term in normalized for term in cls._DATA_REFERENCE_PRONOUNS):
                return True

            if any(
                term in normalized
                for term in (
                    "os dados",
                    "o resultado",
                    "a tabela",
                    "a consulta",
                )
            ):
                return True

        return False

    @classmethod
    def _matches_short_interpretation_command(
        cls,
        normalized: str,
        previous_messages: list | None,
    ) -> bool:
        if not previous_messages or not cls._has_recent_successful_tool_data(previous_messages):
            return False

        for command in cls._INTERPRETATION_SHORT_COMMANDS:
            if normalized == command:
                return True

            if normalized.startswith(f"{command} "):
                tail = normalized[len(command) + 1 :].strip()

                if not tail or any(
                    token in tail
                    for token in (
                        "isso",
                        "isto",
                        "dados",
                        "resultado",
                        "tabela",
                        "consulta",
                        "acima",
                    )
                ):
                    return True

        return False

    @classmethod
    def _has_recent_successful_tool_data(
        cls,
        previous_messages: list,
        *,
        limit: int = 10,
    ) -> bool:
        for item in reversed(previous_messages[-limit:]):
            metadata = item if isinstance(item, dict) else getattr(item, "metadata", None)

            if not isinstance(item, dict):
                metadata = getattr(item, "metadata", None)
            else:
                metadata = item.get("metadata")

            if not isinstance(metadata, dict):
                continue

            for tool_call in metadata.get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if tool_meta.get("ok"):
                    return True

        return False

    @classmethod
    def is_data_reference_without_tool_data(
        cls,
        message: str,
        previous_messages: list | None = None,
    ) -> bool:
        """Pedido de interpretação que referencia dados anteriores, mas sem consulta prévia."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if cls._has_recent_successful_tool_data(previous_messages or []):
            return False

        if any(term in normalized for term in cls._DATA_REFERENCE_TERMS):
            return True

        if "acima" in normalized and any(
            term in normalized for term in cls._DATA_INTERPRETATION_TERMS
        ):
            return True

        return normalized in cls._INTERPRETATION_SHORT_COMMANDS

    @classmethod
    def is_comparison_or_insight_request(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if cls._looks_like_single_product_fetch(normalized):
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
    def _looks_like_single_product_fetch(cls, normalized: str) -> bool:
        if any(
            term in normalized
            for term in (
                "ficha completa",
                "analise completa",
                "análise completa",
                "informacoes completas",
                "informações completas",
                "analisador do produto",
                "analisador completo",
            )
        ):
            return "compar" not in normalized and "versus" not in normalized

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

                if ChatProductQueryIntentService._is_date_numeric_token(match.group(0)):
                    continue

                if ChatProductQueryIntentService._is_example_product_code_token(raw, match):
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
        *,
        previous_messages: list | None = None,
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

        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        if (
            ChatProductQueryIntentService.references_previous_product(message)
            or ChatRouteContextService.is_product_route_segment(
                ChatRouteContextService.segment_from_message(message)
            )
        ):
            code = ChatProductQueryIntentService.resolve_product_code(
                message,
                conversation_context,
                previous_messages=previous_messages,
            )

            return [code] if code else []

        return []

    @classmethod
    def looks_like_path_placeholder(cls, value: str | None) -> bool:
        token = str(value or "").strip()

        if not token:
            return False

        return bool(cls._PATH_PLACEHOLDER_RE.match(token))

    @classmethod
    def extract_product_code_from_tool_path(cls, path: str | None) -> str | None:
        if not path:
            return None

        match = cls._PRODUCT_PATH_RE.search(str(path))

        if not match:
            return None

        raw_code = str(match.group("code") or "").strip()

        if cls.looks_like_path_placeholder(raw_code):
            return None

        return ChatProductQueryIntentService.normalize_product_code(raw_code)

    @classmethod
    def extract_product_path_segment(cls, path: str | None) -> str | None:
        if not path:
            return None

        match = cls._PRODUCT_PATH_RE.search(str(path))

        if not match or not match.group("segment"):
            return None

        return str(match.group("segment")).strip().lower()
