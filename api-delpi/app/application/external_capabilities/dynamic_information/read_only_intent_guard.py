"""Explicit mutation intent guard for READ-only DAVI discovery.

This is a semantic retrieval filter, not AuthZ:
CLEAR EXPLICIT WRITE INTENT → zero READ candidates.
It does not grant/deny permissions and does not create WRITE capabilities.
"""

from __future__ import annotations

from functools import lru_cache

from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.text_normalize import (
    normalize_text,
    tokenize,
)


@lru_cache(maxsize=1)
def _guard_config() -> tuple[frozenset[str], tuple[str, ...]]:
    payload = load_external_read_allowlist()
    raw = payload.get("retrievalReadOnlyGuard") or {}
    verb_tokens: set[str] = set()
    for token in raw.get("writeIntentVerbTokens") or []:
        verb_tokens |= tokenize(str(token))
    phrases = tuple(
        normalize_text(str(phrase))
        for phrase in (raw.get("writeIntentPhrases") or [])
        if str(phrase).strip()
    )
    return frozenset(verb_tokens), phrases


def clear_read_only_intent_guard_cache() -> None:
    _guard_config.cache_clear()


def has_explicit_write_intent(query: str) -> bool:
    """True when the query expresses an explicit mutation command.

    Nouns/participles such as ``atualizacao`` / ``alterado`` / ``aprovacao``
    are intentionally not treated as imperative write verbs.
    """
    text = (query or "").strip()
    if not text:
        return False

    verb_tokens, phrases = _guard_config()
    if not verb_tokens and not phrases:
        return False

    norm = normalize_text(text)
    for phrase in phrases:
        if phrase and phrase in norm:
            return True

    q_tokens = tokenize(text)
    return bool(q_tokens & verb_tokens)
