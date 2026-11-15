"""Citação legível do item de conhecimento da CLARA.

``citation_locator`` continua no retorno para auditoria. O que se
mostra ao usuário é ``display_citation``: nome da fonte e a seção,
sem caminho de arquivo e sem referência interna de documento.
"""

from __future__ import annotations

import re

# Parênteses com referência interna de projeto (doc/docs/GATE/D-…).
_INTERNAL_REF_PAREN = re.compile(
    r"\s*\((?:docs?|GATE|D-)[^)]*\)",
    re.IGNORECASE,
)


def _clean_section(section: str) -> str:
    cleaned = _INTERNAL_REF_PAREN.sub("", section)
    return re.sub(r"\s{2,}", " ", cleaned).strip(" -–—›>")


def display_citation(
    source_title: str,
    citation_locator: dict | None,
    item_title: str = "",
) -> str:
    """Nome da fonte › último nível do heading; sem seção, só o título.

    O sufixo ``#part-N`` é corte interno da ingestão, não uma seção.
    Heading que parece caminho de arquivo não entra na citação.
    Parênteses ``(doc …)`` / ``(docs …)`` / ``(GATE …)`` / ``(D-…)`` saem
    da seção. Se a seção ficar vazia ou igual ao título, só o título.
    """
    title = (source_title or "").strip() or (item_title or "").strip()
    heading = str((citation_locator or {}).get("heading_path") or "").strip()
    if not heading or heading.lower() == "documento":
        return title
    last = heading.split(" > ")[-1].strip()
    section = _clean_section(last.split("#", 1)[0].strip())
    if (
        not section
        or "/" in section
        or "\\" in section
        or section.endswith(".md")
        or section.casefold() == title.casefold()
    ):
        return title
    if not title:
        return section
    return f"{title} › {section}"
