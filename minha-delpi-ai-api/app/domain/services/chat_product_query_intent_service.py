import re


class ChatProductQueryIntent:
    DESCRIPTION = "description"
    STOCK = "stock"
    FULL = "full"


class ChatProductQueryIntentService:
    _ZERO_RECORDS_RE = re.compile(r":\s*0 registro\(s\)\.?$", re.IGNORECASE)
    _PRODUCT_CODE_RE = re.compile(r"\b\d{4,}\b")

    @classmethod
    def detect(cls, message: str) -> str:
        normalized = str(message or "").lower()

        if cls._looks_like_stock_question(normalized):
            return ChatProductQueryIntent.STOCK

        if cls._looks_like_description_question(normalized):
            return ChatProductQueryIntent.DESCRIPTION

        return ChatProductQueryIntent.FULL

    @classmethod
    def references_previous_product(cls, message: str) -> bool:
        normalized = str(message or "").lower()

        terms = [
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
            "dele",
            "dela",
        ]

        return any(term in normalized for term in terms)

    @classmethod
    def extract_product_code(cls, text: str | None) -> str | None:
        match = cls._PRODUCT_CODE_RE.search(str(text or ""))

        if not match:
            return None

        return match.group(0)

    @classmethod
    def resolve_product_code(cls, message: str, conversation_context: str | None = None) -> str | None:
        code = cls.extract_product_code(message)

        if code:
            return code

        normalized = str(message or "").lower()

        if not (
            cls.references_previous_product(message)
            or cls._looks_like_stock_question(normalized)
            or cls._looks_like_description_question(normalized)
        ):
            return None

        return cls.extract_product_code(conversation_context)

    @classmethod
    def format_direct_answer(
        cls,
        humanized: dict,
        *,
        intent: str,
    ) -> str | None:
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
            stock_lines = [
                line
                for line in lines
                if any(
                    token in line.lower()
                    for token in (
                        "filial",
                        "armazém",
                        "armazem",
                        "quantidade",
                        "disponível",
                        "disponivel",
                        "empenhada",
                        "registro(s)",
                    )
                )
            ]
            filtered = stock_lines or lines
            parts = [title] if title else []
            parts.extend(filtered)
            return "\n\n".join(parts)

        filtered = [line for line in lines if not cls._ZERO_RECORDS_RE.search(line)]
        parts = [title] if title else []
        parts.extend(filtered or lines)
        return "\n\n".join(parts)

    @classmethod
    def _looks_like_stock_question(cls, normalized: str) -> bool:
        terms = [
            "estoque",
            "stock",
            "saldo",
            "disponível",
            "disponivel",
            "quantidade dispon",
            "posição de estoque",
            "posicao de estoque",
        ]

        return any(term in normalized for term in terms)

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
        ]

        return any(term in normalized for term in terms)
