"""Contrato da citação legível — N3 + N5R.

display_citation é aditivo. citation_locator não entra nessa string.
"""

from __future__ import annotations

import re
from pathlib import Path

from controllership_finance_app.application.clara.corpus_ingestion import (
    segment_markdown,
)
from controllership_finance_app.application.clara.corpus_manifest import (
    AUTHORIZED_SOURCES,
)
from controllership_finance_app.application.clara.knowledge_citation import (
    display_citation,
)
from controllership_finance_app.interface.mcp.tool_bridge import (
    _readable_citation,
)

_DOCS_ROOT = (
    Path(__file__).resolve().parents[2]
    / "docs/12-roadmap-e-evolucao/controllership-finance"
)
_FORBIDDEN_IN_DISPLAY = re.compile(
    r"(?:\bdoc\s|GATE|CF-|PROC-|/|\.md)",
    re.IGNORECASE,
)


def test_display_citation_uses_source_and_last_heading():
    text = display_citation(
        "Ficha do Fechamento mensal da Controladoria",
        {
            "heading_path": "Identificação > Glossário funcional",
            "document": "fichas/processo-fechamento-ficha.md",
        },
        "Glossário funcional",
    )
    assert text == (
        "Ficha do Fechamento mensal da Controladoria › Glossário funcional"
    )
    assert "/" not in text
    assert ".md" not in text


def test_display_citation_without_heading_is_the_title_only():
    assert display_citation(
        "Base canônica do Fechamento mensal da Controladoria",
        {"heading_path": "documento", "document": "118-base.md"},
    ) == "Base canônica do Fechamento mensal da Controladoria"
    assert display_citation("Fonte", None, "Seção") == "Fonte"


def test_display_citation_drops_file_path_heading():
    text = display_citation(
        "Fonte",
        {"heading_path": "docs/12/arquivo.md", "document": "docs/12/arquivo.md"},
    )
    assert text == "Fonte"
    assert "docs/" not in text


def test_display_citation_strips_internal_doc_ref_from_section():
    text = display_citation(
        "Ficha do Fechamento mensal da Controladoria",
        {
            "heading_path": "Modelo operacional (doc 118 §2)",
            "document": "fichas/processo-fechamento-ficha.md",
        },
    )
    assert text == (
        "Ficha do Fechamento mensal da Controladoria › Modelo operacional"
    )
    assert "doc " not in text


def test_display_citation_strips_compound_doc_refs():
    text = display_citation(
        "Ficha R10 — Despesas por Centro de Custo",
        {
            "heading_path": (
                "Regras de negócio (doc 85 §10 + doc 126 §§14–19)"
            ),
            "document": "fichas/R10-ficha.md",
        },
    )
    assert text == "Ficha R10 — Despesas por Centro de Custo › Regras de negócio"
    assert "doc " not in text


def test_display_citation_dedupes_section_equal_to_title():
    title = "Ficha do Fechamento mensal da Controladoria"
    text = display_citation(
        title,
        {"heading_path": title, "document": "fichas/processo-fechamento-ficha.md"},
    )
    assert text == title
    assert " › " not in text


def test_readable_citation_keeps_locator_and_hides_path():
    item = _readable_citation(
        {
            "title": "Identificação",
            "source_name": "Ficha do Fechamento mensal da Controladoria",
            "citation_locator": {
                "document": "fichas/processo-fechamento-ficha.md",
                "heading_path": "Identificação#part-2",
            },
        }
    )
    assert item["source_title"].startswith("Ficha do")
    assert item["display_citation"] == (
        "Ficha do Fechamento mensal da Controladoria › Identificação"
    )
    assert "part-" not in item["display_citation"]
    assert ".md" not in item["display_citation"]


def test_published_display_citations_have_no_internal_refs():
    """Percorre as fontes do manifesto e falha se display_citation
    carregar referência interna (doc/GATE/CF-/PROC-/caminho)."""
    offenders: list[str] = []
    for spec in AUTHORIZED_SOURCES:
        path = _DOCS_ROOT / spec.path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for segment in segment_markdown(text):
            citation = display_citation(
                spec.name,
                {
                    "document": spec.path,
                    "heading_path": segment.heading_path,
                },
                segment.heading_path.split(" > ")[-1],
            )
            if _FORBIDDEN_IN_DISPLAY.search(citation):
                offenders.append(
                    f"{spec.source_id}:{segment.heading_path} → {citation}"
                )
    assert not offenders, "display_citation com ref interna:\n" + "\n".join(
        offenders[:20]
    )
