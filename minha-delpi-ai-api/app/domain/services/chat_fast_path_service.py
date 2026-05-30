import re
import unicodedata

from app.domain.services.chat_small_talk_pattern_service import ChatSmallTalkPatternService

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


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


class ChatFastPathService:
    @staticmethod
    def is_small_talk(message: str) -> bool:
        return ChatSmallTalkPatternService.is_small_talk(message)

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

        if ChatFastPathService.is_small_talk(text):
            return True

        if len(text) > max(1, max_chars):
            return False

        normalized = _normalize_text(text)

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
