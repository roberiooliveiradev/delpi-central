"""Integridade das fichas CLARA R12/R15 — regressão Gate 073/074.

Detecta a corrupção produzida por patch destrutivo (string splice
``para rotinas (visão read-only)`` em separadores/datas/identificadores)
e valida estrutura mínima do markdown.
"""
from pathlib import Path

FICHAS = (
    Path(__file__).resolve().parents[2]
    / "docs/12-roadmap-e-evolucao/controllership-finance/fichas"
)


def test_no_corruption_splice_in_r12_r15():
    for name in ("R12-ficha.md", "R15-ficha.md"):
        text = (FICHAS / name).read_text(encoding="utf-8")
        assert "para rotinas (visão read-only)" not in text, name


def test_dates_and_identifiers_intact():
    r12 = (FICHAS / "R12-ficha.md").read_text(encoding="utf-8")
    assert "MATA320" in r12 and "cost-closing-state" in r12
    r15 = (FICHAS / "R15-ficha.md").read_text(encoding="utf-8")
    assert "MATA330" in r15 and "MATA280" in r15
    # datas não podem estar fatiadas por texto arbitrário
    for text in (r12, r15):
        assert "para rotinas" not in text
