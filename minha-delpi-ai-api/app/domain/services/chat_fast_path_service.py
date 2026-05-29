import re
import unicodedata


_SMALL_TALK_PATTERN = (
    r"^(ol[aá]|oi|opa|eae|e a[ií]|hey|hi|hello|"
    r"bom dia|boa tarde|boa noite|"
    r"tudo bem|td bem|como vai|blz|beleza|"
    r"obrigad[oa]|valeu|vlw|brigad[oa]|"
    r"ok|okay|sim|n[aã]o|nao|"
    r"at[eé]|tchau|flw|falou)"
    r"[\s!?.,:;]*$"
)
_SMALL_TALK_RE = re.compile(_SMALL_TALK_PATTERN, re.IGNORECASE)

_KNOWLEDGE_HINT_PATTERN = (
    r"\?|"
    r"\b(como|quando|onde|qual|quais|quanto|quantos|quem|por que|porque|"
    r"explique|detalhe|liste|mostre|busque|consulte|informa|produto|"
    r"estoque|pedido|pedidos|nota|sql|api|relat[oó]rio|documento|"
    r"fornecedor|fornecedores|cliente|clientes|pre[cç]o|venda|vendas|compra|compras|fatura|"
    r"estrutura|roteiro|inspe[cç][aã]o|movimenta|"
    r"agente|projeto|ajud[ae]|configur|permiss|acesso|"
    r"capacidad|funcionalidad|comando|ferramenta|api|action|"
    r"ver|listar|exib[ai]r|abrir)\b"
)
_KNOWLEDGE_HINT_RE = re.compile(_KNOWLEDGE_HINT_PATTERN, re.IGNORECASE)

_OPERATIONAL_HINT_RE = re.compile(
    r"\b(\d{5,}|[A-Z]{2,}\d{3,})\b"
)

_REFINEMENT_HINT_RE = re.compile(
    r"\b("
    r"proxima pagina|pagina anterior|pagina seguinte|"
    r"filial|armazem|filtre|filtro|filtrar|"
    r"aumente para|mais linhas|mais registros|"
    r"completo de novo|estoque completo|mostre completo"
    r")\b",
    re.IGNORECASE,
)


_SMALL_TALK_EXTENDED_PATTERN = (
    r"^(ol[aá]|oi|opa|hey|hi|hello|bom dia|boa tarde|boa noite)"
    r"[\s,!?]*"
    r"(tudo bem|td bem|como vai|blz|beleza)?"
    r"[\s!?.,:;]*$"
)
_SMALL_TALK_EXTENDED_RE = re.compile(_SMALL_TALK_EXTENDED_PATTERN, re.IGNORECASE)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


class ChatFastPathService:
    @staticmethod
    def is_small_talk(message: str) -> bool:
        text = str(message or "").strip()

        if not text:
            return False

        normalized = _normalize_text(text)

        if _SMALL_TALK_RE.match(normalized):
            return True

        return bool(_SMALL_TALK_EXTENDED_RE.match(normalized))

    @staticmethod
    def should_use(
        message: str,
        *,
        enabled: bool = True,
        max_chars: int = 30,
        attachment_ids: list[str] | None = None,
    ) -> bool:
        if not enabled:
            return False

        if attachment_ids:
            return False

        text = str(message or "").strip()

        if not text:
            return False

        if len(text) > max(1, max_chars):
            return False

        normalized = _normalize_text(text)

        if ChatFastPathService.is_small_talk(text):
            return True

        if _KNOWLEDGE_HINT_RE.search(normalized):
            return False

        if _OPERATIONAL_HINT_RE.search(text):
            return False

        if _REFINEMENT_HINT_RE.search(normalized):
            return False

        if normalized in {"ajuda", "help", "comandos", "capacidades", "funcionalidades"}:
            return False

        word_count = len(normalized.split())

        return word_count <= 2 and not normalized.endswith("?")
