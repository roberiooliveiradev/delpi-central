"""Contrato da citação legível — N3.

display_citation é aditivo. citation_locator não entra nessa string.
"""

from controllership_finance_app.application.clara.knowledge_citation import (
    display_citation,
)
from controllership_finance_app.interface.mcp.tool_bridge import (
    _readable_citation,
)


def test_display_citation_uses_source_and_last_heading():
    text = display_citation(
        "Ficha do Fechamento mensal da Controladoria",
        {"heading_path": "Identificação > Glossário funcional", "document": "fichas/processo-fechamento-ficha.md"},
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
