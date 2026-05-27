import re
import unicodedata


_TYPO_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bforncedor(es)?\b", r"fornecedor\1"),
    (r"\bfornecedore(s)?\b", r"fornecedor\1"),
    (r"\bclinte(s)?\b", r"cliente\1"),
    (r"\bestoq(u|ue)?\b", r"estoque"),
    (r"\bestq\b", r"estoque"),
    (r"\bprodt?\b", r"produto"),
    (r"\bdescriçao\b", r"descricao"),
    (r"\brotiero\b", r"roteiro"),
    (r"\binspeçao\b", r"inspecao"),
    (r"\bmovimentaçao\b", r"movimentacao"),
    (r"\bmovimentaçoes\b", r"movimentacoes"),
    (r"\brelatório\b", r"relatorio"),
    (r"\brelatorio\b", r"relatorio"),
    (r"\bpreço\b", r"preco"),
    (r"\bpais\b", r"pais"),
    (r"\bpai\b", r"pai"),
)

_TYPO_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), repl) for pattern, repl in _TYPO_REPLACEMENTS
]


class ChatMessageNormalizationService:
    """Normaliza mensagens do usuário para matching de intenção (acentos, typos)."""

    @staticmethod
    def strip_accents(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(value or "").strip().lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    @classmethod
    def normalize_for_matching(cls, message: str) -> str:
        text = cls.strip_accents(message)
        text = re.sub(r"\s+", " ", text).strip()

        for pattern, replacement in _TYPO_PATTERNS:
            text = pattern.sub(replacement, text)

        return text

    @classmethod
    def contains_any(cls, message: str, terms: tuple[str, ...] | list[str]) -> bool:
        normalized = cls.normalize_for_matching(message)
        return any(cls.strip_accents(term) in normalized for term in terms)
