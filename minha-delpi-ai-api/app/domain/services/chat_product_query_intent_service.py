import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatProductQueryIntent:
    DESCRIPTION = "description"
    SUMMARY = "summary"
    STOCK = "stock"
    STRUCTURE = "structure"
    PARENTS = "parents"
    FULL = "full"


class ChatProductQueryIntentService:
    _ZERO_RECORDS_RE = re.compile(r":\s*0 registro\(s\)\.?$", re.IGNORECASE)
    _PRODUCT_CODE_RE = re.compile(
        r"\b(?:\d[\d.\-/]{2,}\d|\d{4,})\b",
    )

    @classmethod
    def detect(cls, message: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if cls._looks_like_mixed_documental_operational(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_parents_question(normalized):
            return ChatProductQueryIntent.PARENTS

        if cls._looks_like_structure_question(normalized):
            return ChatProductQueryIntent.STRUCTURE

        if cls._looks_like_stock_question(normalized):
            return ChatProductQueryIntent.STOCK

        if cls._looks_like_product_summary_question(normalized):
            return ChatProductQueryIntent.SUMMARY

        if cls._looks_like_description_question(normalized):
            return ChatProductQueryIntent.DESCRIPTION

        return ChatProductQueryIntent.FULL

    @classmethod
    def _looks_like_mixed_documental_operational(cls, normalized: str) -> bool:
        documental_terms = (
            "explique",
            "explica ",
            "documentação",
            "documentacao",
            "política",
            "politica",
            "procedimento",
            "como funciona",
            "manual ",
        )
        operational_terms = (
            "estoque",
            "produto",
            "saldo",
            "lmp",
        )

        return any(term in normalized for term in documental_terms) and any(
            term in normalized for term in operational_terms
        )

    @classmethod
    def references_previous_product(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        terms = [
            "filtre",
            "filtro",
            "filtrar",
            "filtra ",
            "mostre só",
            "mostre so",
            "só a filial",
            "so a filial",
            "apenas filial",
            "somente filial",
            "desse produto",
            "deste produto",
            "esse produto",
            "este produto",
            "do produto",
            "da produto",
            "mesmo produto",
            "produto acima",
            "produto anterior",
            "código acima",
            "codigo acima",
            "desse item",
            "deste item",
            "esse item",
            "mesmo código",
            "mesmo codigo",
            "mesma referência",
            "mesma referencia",
            "dele",
            "dela",
            "sobre o produto",
            "sobre o item",
            "sobre esse",
            "sobre este",
        ]

        return any(term in normalized for term in terms) or cls._looks_like_product_followup(
            normalized
        )

    @classmethod
    def _looks_like_product_followup(cls, normalized: str) -> bool:
        followup_terms = [
            "o que mais",
            "que mais",
            "mais informações",
            "mais informacoes",
            "outras informações",
            "outras informacoes",
            "algo mais",
            "mais sobre",
            "mais dados",
            "mais detalhes",
            "o que mais pode",
            "o que mais tem",
            "o que mais sabe",
            "o que mais consegue",
        ]
        product_terms = [
            "produto",
            "item",
            "material",
            "código",
            "codigo",
        ]

        has_followup = any(term in normalized for term in followup_terms)
        has_product_ref = any(term in normalized for term in product_terms)

        return has_followup and has_product_ref

    @classmethod
    def normalize_product_code(cls, raw: str) -> str:
        digits = re.sub(r"\D", "", str(raw or ""))

        if len(digits) >= 4:
            return digits

        return str(raw or "").strip()

    @classmethod
    def extract_product_code(cls, text: str | None) -> str | None:
        if cls._looks_like_lmp_context(text):
            return None

        raw = str(text or "")

        for match in cls._PRODUCT_CODE_RE.finditer(raw):
            if cls._is_group_code_numeric_token(raw, match):
                continue

            return cls.normalize_product_code(match.group(0))

        return None

    @classmethod
    def _is_group_code_numeric_token(cls, text: str, match: re.Match[str]) -> bool:
        """Evita confundir «grupo 1008» com código de produto 1008."""
        prefix = text[max(0, match.start() - 48) : match.start()].lower()

        if re.search(
            r"(?:\bgrupo|\bgroup_code|\bdo\s+grupo|\bpelo\s+grupo|\bde\s+grupo)\s*$",
            prefix,
            flags=re.IGNORECASE,
        ):
            return True

        if re.search(r"\bgrupo\s+de\s+produtos?\s*$", prefix, flags=re.IGNORECASE):
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(text)

        if "grupo" in normalized and re.search(
            rf"\bgrupo\s+{re.escape(match.group(0).lower())}\b",
            normalized,
        ):
            return True

        return False

    @classmethod
    def _looks_like_lmp_context(cls, text: str | None) -> bool:
        normalized = str(text or "").lower()

        return any(
            term in normalized
            for term in (
                "lmp",
                "lmps",
                "lista de materiais de projeto",
                "ordem de venda",
                " amostra",
                " ov ",
                " ov#",
            )
        )

    @classmethod
    def extract_last_product_code(cls, text: str | None) -> str | None:
        raw = str(text or "")
        last_code: str | None = None

        for match in cls._PRODUCT_CODE_RE.finditer(raw):
            if cls._is_group_code_numeric_token(raw, match):
                continue

            last_code = cls.normalize_product_code(match.group(0))

        return last_code

    @classmethod
    def extract_last_product_code_from_messages(
        cls,
        previous_messages: list | None,
    ) -> str | None:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        for item in reversed((previous_messages or [])[-16:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
                    str(tool_meta.get("path") or "")
                )

                if code:
                    return code

            content = cls._message_content(item)
            code = cls.extract_product_code(content)

            if code:
                return code

        return None

    @classmethod
    def infer_intent_from_recent_tool(cls, previous_messages: list | None) -> str | None:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        segment_to_intent = {
            "stock": ChatProductQueryIntent.STOCK,
            "summary": ChatProductQueryIntent.SUMMARY,
            "structure": ChatProductQueryIntent.STRUCTURE,
            "parents": ChatProductQueryIntent.PARENTS,
        }

        for item in reversed((previous_messages or [])[-12:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                segment = ChatAnalysisIntentService.extract_product_path_segment(
                    str(tool_meta.get("path") or "")
                )

                if segment in segment_to_intent:
                    return segment_to_intent[segment]

        return None

    @classmethod
    def resolve_product_intent(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> str:
        intent = cls.detect(message)

        if intent != ChatProductQueryIntent.FULL:
            return intent

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if cls._looks_like_product_sub_intent(normalized):
            return intent

        inherited = cls.infer_intent_from_recent_tool(previous_messages)

        if not inherited:
            return intent

        if cls.extract_product_code(message) or cls.references_previous_product(message):
            return inherited

        return inherited

    @classmethod
    def resolve_product_code(
        cls,
        message: str,
        conversation_context: str | None = None,
        *,
        previous_messages: list | None = None,
    ) -> str | None:
        code = cls.extract_product_code(message)

        if code:
            return code

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not (
            cls.references_previous_product(message)
            or cls._looks_like_stock_question(normalized)
            or cls._looks_like_stock_scope_reset_question(normalized)
            or cls._looks_like_description_question(normalized)
            or cls._looks_like_product_summary_question(normalized)
            or cls._looks_like_structure_question(normalized)
            or cls._looks_like_parents_question(normalized)
            or cls._looks_like_product_sub_intent(normalized)
        ):
            return None

        if previous_messages:
            code = cls.extract_last_product_code_from_messages(previous_messages)

            if code:
                return code

        if conversation_context:
            return cls.extract_last_product_code(conversation_context)

        return None

    @classmethod
    def _message_metadata(cls, message) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}

    @classmethod
    def _message_content(cls, message) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")

    @classmethod
    def format_direct_answer(
        cls,
        humanized: dict,
        *,
        intent: str,
    ) -> str | None:
        if intent == ChatProductQueryIntent.STRUCTURE:
            from app.domain.services.chat_product_structure_presentation_service import (
                ChatProductStructurePresentationService,
            )

            dados = humanized.get("dados")

            if isinstance(dados, dict):
                formatted = ChatProductStructurePresentationService.format_markdown(
                    dados,
                    source_path=humanized.get("sourcePath"),
                )

                if formatted:
                    return formatted

        lines = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line).strip()
        ]

        if not lines:
            return None

        title = str(humanized.get("titulo") or "").strip()

        if intent == ChatProductQueryIntent.DESCRIPTION:
            parts = [title] if title else []
            parts.append(lines[0])
            return "\n\n".join(parts)

        if intent == ChatProductQueryIntent.STOCK:
            stock_lines = cls._filter_stock_lines(lines)
            filtered = [
                line
                for line in (stock_lines or lines)
                if not cls._ZERO_RECORDS_RE.search(line)
            ]

            if not filtered:
                return None

            header = title or "Posição de estoque"
            body = "\n".join(f"- {line}" for line in filtered[:12])

            if len(filtered) > 12:
                body += f"\n- … e mais {len(filtered) - 12} registro(s)."

            return f"**{header}**\n\n{body}"

        filtered = [line for line in lines if not cls._ZERO_RECORDS_RE.search(line)]
        parts = [title] if title else []
        parts.extend(filtered or lines)
        return "\n\n".join(parts)

    @classmethod
    def _filter_stock_lines(cls, lines: list[str]) -> list[str]:
        stock_lines = []

        for line in lines:
            lowered = line.lower()

            if any(
                token in lowered
                for token in (
                    "filial",
                    "armazém",
                    "armazem",
                    "quantidade",
                    "disponível",
                    "disponivel",
                    "empenhada",
                    "reservada",
                    "registro(s)",
                    "local:",
                    "localização",
                    "localizacao",
                )
            ):
                stock_lines.append(line)

        return stock_lines

    @classmethod
    def _looks_like_stock_scope_reset_question(cls, normalized: str) -> bool:
        return any(
            term in normalized
            for term in (
                "completo de novo",
                "estoque completo",
                "todas as filiais",
                "todas filiais",
                "mostre completo",
                "mostra completo",
                "sem filtro",
                "sem filial",
            )
        )

    @classmethod
    def _looks_like_stock_question(cls, normalized: str) -> bool:
        if any(
            term in normalized
            for term in (
                "valor total",
                "valor de estoque",
                "valor do estoque",
                "giro de estoque",
            )
        ) and not cls.extract_product_code(normalized):
            return False

        terms = [
            "estoque",
            "stock",
            "saldo",
            "disponível",
            "disponivel",
            "quantidade dispon",
            "posição de estoque",
            "posicao de estoque",
            "tem em estoque",
            "qtd dispon",
            "posição",
            "posicao",
        ]

        return any(term in normalized for term in terms)

    @classmethod
    def _looks_like_product_summary_question(cls, normalized: str) -> bool:
        if any(
            term in normalized
            for term in (
                "resumo de venda",
                "resumo de vendas",
                "resumo de kaizen",
                "resumo de kaizens",
                "resumo do kaizen",
                "kaizens do mes",
                "kaizens do mês",
            )
        ):
            return False

        if any(
            term in normalized
            for term in (
                "resumo do produto",
                "resumo sintetico",
                "resumo sintético",
                "visao resumida do produto",
                "visão resumida do produto",
                "visao resumida do item",
                "visão resumida do item",
            )
        ):
            return True

        if "resumo" not in normalized:
            return False

        if any(
            term in normalized
            for term in (
                "ficha completa",
                "analisador",
                "analyzer",
                "analise completa",
                "análise completa",
                "informacoes completas",
                "informações completas",
                "tudo sobre o produto",
            )
        ):
            return False

        return any(
            term in normalized
            for term in (
                "produto",
                "item",
                "material",
                "codigo",
                "código",
            )
        )

    @classmethod
    def _looks_like_description_question(cls, normalized: str) -> bool:
        terms = [
            "descrição",
            "descricao",
            "description",
            "nome do produto",
            "como se chama",
            "qual a descrição",
            "qual a descricao",
            "qual produto",
            "referência",
            "referencia",
            "ref ",
            " ref.",
            "sku",
            "código do item",
            "codigo do item",
            "o que é o produto",
            "o que e o produto",
            "detalhes do produto",
            "detalhe do produto",
            "dados do produto",
            "dados cadastrais",
            "cadastro do produto",
            "me fale sobre o",
            "me fale do",
            "informações do produto",
            "informacoes do produto",
            "informações completas",
            "informacoes completas",
        ]

        return any(term in normalized for term in terms)

    @classmethod
    def _looks_like_parents_question(cls, normalized: str) -> bool:
        terms = (
            "onde é usado",
            "onde e usado",
            "onde é utilizado",
            "onde e utilizado",
            "produto pai",
            "produtos pai",
            "itens pai",
            "item pai",
            "parent",
            "parents",
            "where used",
            "utilizado em",
            "usado em",
            "aplicação do produto",
            "aplicacao do produto",
            "onde usa ",
            "onde utiliza",
            "é usado em",
            "e usado em",
            "em quais produtos é usado",
            "em quais produtos e usado",
            "em quais itens é usado",
            "em quais itens e usado",
            "quem usa o",
            "quem utiliza o",
            "faz parte de",
            "componente de qual",
            "pai do",
            "pais do",
            "quais produtos usam",
            "quais itens usam",
            "produtos que usam",
            "itens que usam",
        )
        return any(term in normalized for term in terms)

    @classmethod
    def _looks_like_structure_question(cls, normalized: str) -> bool:
        terms = [
            "estrutura",
            "bom",
            "bill of material",
            "composição",
            "composicao",
            "componentes",
            "árvore do produto",
            "arvore do produto",
        ]

        return any(term in normalized for term in terms)

    @classmethod
    def _looks_like_product_sub_intent(cls, normalized: str) -> bool:
        """Reconhece perguntas sobre aspectos específicos de um produto que
        implicam necessidade de código (ex: 'qual o roteiro?', 'fornecedores?')."""
        terms = [
            "roteiro",
            "guide",
            "fornecedor",
            "fornecedore",
            "supplier",
            "preço",
            "preco",
            "pricing",
            "quanto custa",
            "custo do",
            "compra",
            "purchase",
            "venda",
            "faturamento",
            "carteira",
            "movimentaç",
            "movimentac",
            "inspeção",
            "inspecao",
            "nota de entrada",
            "nota de saída",
            "nota de saida",
            "notas de entrada",
            "notas de saída",
            "notas de saida",
            "fiscal",
            "nfe",
            "cliente",
            "customer",
            "pai",
            "parent",
            "where used",
        ]

        return any(term in normalized for term in terms)
