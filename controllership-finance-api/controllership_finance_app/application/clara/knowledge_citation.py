"""Citação legível do item de conhecimento da CLARA.

``citation_locator`` continua no retorno para auditoria. O que se
mostra ao usuário é ``display_citation``: nome da fonte e a seção,
sem caminho de arquivo.
"""

from __future__ import annotations


def display_citation(
    source_title: str,
    citation_locator: dict | None,
    item_title: str = "",
) -> str:
    """Nome da fonte › último nível do heading; sem seção, só o título.

    O sufixo ``#part-N`` é corte interno da ingestão, não uma seção.
    Heading que parece caminho de arquivo não entra na citação.
    """
    title = (source_title or "").strip() or (item_title or "").strip()
    heading = str((citation_locator or {}).get("heading_path") or "").strip()
    if not heading or heading.lower() == "documento":
        return title
    last = heading.split(" > ")[-1].strip()
    section = last.split("#", 1)[0].strip()
    if (
        not section
        or "/" in section
        or "\\" in section
        or section.endswith(".md")
    ):
        return title
    if not title:
        return section
    return f"{title} › {section}"
