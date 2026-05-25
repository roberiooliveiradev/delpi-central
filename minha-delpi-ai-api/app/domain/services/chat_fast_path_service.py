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
    r"\b(como|quando|onde|qual|quais|quanto|quantos|por que|porque|"
    r"explique|detalhe|liste|mostre|busque|consulte|informa|produto|"
    r"estoque|pedido|nota|sql|api|relat[oó]rio|documento)\b"
)
_KNOWLEDGE_HINT_RE = re.compile(_KNOWLEDGE_HINT_PATTERN, re.IGNORECASE)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


class ChatFastPathService:
    @staticmethod
    def should_use(
        message: str,
        *,
        enabled: bool = True,
        max_chars: int = 48,
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

        if _SMALL_TALK_RE.match(normalized):
            return True

        if _KNOWLEDGE_HINT_RE.search(normalized):
            return False

        word_count = len(normalized.split())

        return word_count <= 3 and not normalized.endswith("?")
