"""Conservative concept-only retrieval routing for DAVI.

A pure conceptual query should use governed Knowledge, not an unrelated
operational READ candidate. This lexical gate does not interpret concepts,
answer questions, control tool execution, or replace backend business AuthZ.

Ambiguous or mixed data+concept questions stay eligible for discovery and
remain bound by the existing allowlist, candidate token and backend AuthZ.
"""

from __future__ import annotations

import re

from app.application.external_capabilities.dynamic_information.text_normalize import (
    normalize_text,
)

# Syntax-level, language-aware intent markers. No domain terms or operationIds.
_CONCEPT_ONLY_START = re.compile(
    r"^(?:"
    r"o que significa\b|que significa\b|"
    r"qual (?:e )?o significado (?:de|do|da|das|dos)\b|"
    r"o que quer dizer\b|"
    r"qual (?:e )?o conceito (?:de|do|da)\b|"
    r"explique (?:o|a) conceito (?:de|do|da)\b|"
    r"defina\b|"
    r"qual (?:e )?a diferenca entre\b|"
    r"quais (?:sao )?as diferencas entre\b|"
    r"what does\b|what is the difference between\b|"
    r"define\b"
    r")"
)

# Deliberately fail OPEN for mixed questions: the operational half still
# belongs to authorized discover→execute, not to the Knowledge-only gate.
_MIXED_REQUEST = re.compile(
    r"\b(?:e|tambem|alem disso|and|also)\s+"
    r"(?:me\s+)?(?:qual|quais|quanto|quantos|quantas|"
    r"mostre|liste|consulte|busque|verifique|"
    r"calcule|traga|informe|diga|show|list|check|calculate)\b"
)

_CURRENT_WINDOW = re.compile(
    r"\b(?:hoje|agora|ontem|amanha|"
    r"neste mes|deste mes|mes passado|"
    r"na proxima semana|semana passada|"
    r"ultimos [0-9]+ dias|today|now|yesterday|tomorrow|this month|last month)\b"
)


def is_pure_concept_intent(query: str) -> bool:
    """Return True only for unequivocally conceptual *single-intent* syntax.

    This is a conservative UI/retrieval hint, NOT knowledge authority.
    False negatives (ambiguous text) are preferable to suppressing a legitimate
    time-windowed data read. No business terms, entity IDs or hidden RBAC.
    """
    normalized = normalize_text(query or "").strip()
    if not normalized or len(normalized) > 240:
        return False
    if not _CONCEPT_ONLY_START.search(normalized):
        return False
    if _MIXED_REQUEST.search(normalized) or _CURRENT_WINDOW.search(normalized):
        return False
    return True
