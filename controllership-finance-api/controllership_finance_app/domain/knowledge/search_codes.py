"""Códigos citados numa pergunta de conhecimento (TES, CFOP, grupo).

Função pura: não consulta banco e não decide ranking. O repositório
recebe a lista e monta o passe. Sem código, a busca permanece a
atual (AND e, se faltar, OR).
"""

from __future__ import annotations

import re

# Datas e competências saem antes dos tokens, para 2026-10, 10/2026
# e 14/11 não virarem código. R10/R05 ficam colados à letra do
# relatório e também saem. Anos 20xx são filtrados depois, no token
# de 4 dígitos (outubro 2026).
_MASK = re.compile(
    r"\d{4}-\d{2}(?:-\d{2})?"
    r"|\d{1,2}/\d{4}"
    r"|\d{1,2}/\d{1,2}(?:/\d{2,4})?"
    r"|\bR\d{2,}\b",
    re.IGNORECASE,
)
# 4 dígitos antes de 3, para 5124 não ser lido como 512.
# 3A8 é dígito-letra-dígito. 525 é o TES de 3 dígitos.
_TOKEN = re.compile(r"\b(\d{4}|\d[A-Za-z]\d|\d{3})\b")
_YEAR = re.compile(r"20\d{2}")


def extract_search_codes(query: str | None) -> list[str]:
    """Códigos na ordem do texto. Lista vazia quando não há código."""
    if not query:
        return []
    masked = _MASK.sub(" ", query)
    found: list[str] = []
    seen: set[str] = set()
    for match in _TOKEN.finditer(masked):
        code = match.group(1).upper()
        if _YEAR.fullmatch(code) or code in seen:
            continue
        seen.add(code)
        found.append(code)
    return found
