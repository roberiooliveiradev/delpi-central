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
    r"como funciona(?:m)?\b|"
    r"como (?:se )?interpreta(?:r)?\b|"
    r"quais? (?:sao )?(?:as |os )?(?:normas?|regras?|padroes?|padrao|"
    r"diretrizes?|convencoes?|abrevia\w*|siglas?|terminologias?|"
    r"nomenclaturas?|documentac\w*|manuais?|codifica\w*)\b|"
    r"(?:existe|ha) (?:uma |um |alguma )?(?:norma|padrao|diretriz|convencao|"
    r"regra|documentacao|guia)\b|"
    # Telegraphic document-seeking starts: the query opens with document
    # vocabulary (optionally after a consult/read request verb) instead of a
    # question marker — "normas de codificacao…", "consultar guia tecnico…".
    # Still syntax-level: no domain terms, entity names or operationIds.
    r"(?:consultar|consulte|consulta|buscar|busque|busca|leia|ler|"
    r"localize|procure|verifique|verificar)?\s*"
    r"(?:as |os |a |o |uma |um |sobre |de |da |do )?\s*"
    r"(?:normas?|regras?|padroes?|padrao|diretrizes?|convencoes?|"
    r"nomenclaturas?|documentac\w*|manuais?|guias?|codifica\w*|"
    r"descricao (?:tecnica|normativa|padrao)|instrucoes (?:tecnicas|de "
    r"operacao))\b|"
    r"what does\b|what is the difference between\b|"
    r"how (?:does|do)\b|are there (?:any )?(?:rules|standards|guidelines)\b|"
    r"(?:show|list|get|read) (?:me )?(?:the )?(?:rules|standards|"
    r"guidelines|conventions|nomenclature|documentation|manual)\b|"
    r"define\b"
    r")"
)

# Deliberately fail OPEN for mixed questions: the operational half still
# belongs to authorized discover→execute, not to the Knowledge-only gate.
_MIXED_REQUEST = re.compile(
    r"\b(?:e|tambem|alem disso|and|also)\s+"
    r"(?:me\s+)?(?:qual|quais|quanto|quantos|quantas|"
    r"mostre|liste|consulte|busque|verifique|"
    r"encontre|localize|procure|obtenha|retorne|exiba|apresente|"
    r"calcule|traga|informe|diga|show|list|check|calculate|find)\b"
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
