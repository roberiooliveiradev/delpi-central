import re
from pathlib import Path


def test_adr_readme_lists_all_markdown_files():
    adr_dir = Path("docs/architecture/adr")
    readme = (adr_dir / "README.md").read_text(encoding="utf-8")
    adr_files = sorted(
        path.name
        for path in adr_dir.glob("*.md")
        if path.name != "README.md"
    )

    assert adr_files, "expected at least one ADR markdown file"

    for name in adr_files:
        assert name in readme, f"{name} missing from adr/README.md"


def test_adr_files_have_required_sections():
    adr_dir = Path("docs/architecture/adr")
    required = ("## Contexto", "## Decisão", "## Consequências")

    for path in sorted(adr_dir.glob("*.md")):
        if path.name == "README.md":
            continue

        content = path.read_text(encoding="utf-8")
        for section in required:
            assert section in content, f"{path.name} missing {section}"


def test_chat_intelligence_base_links_adr_index():
    doc = Path("docs/architecture/chat-intelligence-base.md").read_text(encoding="utf-8")

    assert "## Índice de sub-sistemas" in doc
    assert "./adr/README.md" in doc
