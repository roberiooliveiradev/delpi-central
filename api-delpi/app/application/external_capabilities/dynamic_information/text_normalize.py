"""Text normalization for DAVI lexical retrieval (PT-BR + EN, accent-insensitive)."""

from __future__ import annotations

import re
import unicodedata

_TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def normalize_text(text: str) -> str:
    """Lowercase + NFKD accent fold + whitespace collapse."""
    raw = unicodedata.normalize("NFKD", text or "")
    folded = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return " ".join(folded.lower().split())


def tokenize(text: str) -> set[str]:
    """Tokenize after accent-insensitive normalization; drop single-char noise."""
    return set(ordered_tokens(text))


def ordered_tokens(text: str) -> list[str]:
    """Ordered tokens after accent-insensitive normalization; drop single-char noise."""
    return [t for t in _TOKEN_RE.findall(normalize_text(text)) if len(t) > 1]


# Portuguese function/filler words that often appear between durable semantic
# tokens in natural questions without changing phrase identity.
# Intentionally excludes content markers such as ``por`` (OTD por cliente) and
# ``mais`` (clientes mais faturaram).
_PHRASE_FILLERS = frozenset(
    {
        "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do",
        "dos", "e", "em", "essa", "esse", "esta", "este", "estes", "estas",
        "esta", "estao", "foi", "foram", "ja", "lhe", "liste", "longo",
        "me", "mostre", "na", "nas", "neste", "nesta", "no", "nos",
        "nossa", "nossas", "nosso", "nossos", "o", "os", "ou", "para",
        "pela", "pelas", "pelo", "pelos", "que", "quero", "se", "sem",
        "sua", "suas", "um", "uma", "umas", "uns", "ver", "veio", "vieram",
    }
)


def tokens_compatible(left: str, right: str) -> bool:
    """Conservative PT singular/plural and shared-stem compatibility."""
    if left == right:
        return True
    if len(left) > 3 and len(right) > 3:
        left_stem = left[:-1] if left.endswith("s") and not left.endswith("ss") else left
        right_stem = (
            right[:-1] if right.endswith("s") and not right.endswith("ss") else right
        )
        if left_stem == right_stem:
            return True
    # Verb/noun derivation pairs (faturamos/faturamento, evoluiu/evolucao).
    if len(left) >= 5 and len(right) >= 5 and left[:5] == right[:5]:
        suffixes = ("mos", "ram", "iu", "ou", "cao", "sao", "mento", "veis")
        if any(left.endswith(suf) or right.endswith(suf) for suf in suffixes):
            return True
    # Shared 6-char prefix covers gerund/flexion families (entregando/entrega,
    # consultando/consulta) without uncontrolled stemming on short tokens.
    if len(left) >= 6 and len(right) >= 6 and left[:6] == right[:6]:
        return True
    return False
