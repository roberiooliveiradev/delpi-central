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
