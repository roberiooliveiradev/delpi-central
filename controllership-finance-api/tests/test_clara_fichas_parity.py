"""CLARA-KNOWLEDGE stage-04 — paridade estrutural das fichas R01–R15.

Garante que as 15 fichas técnicas existem, seguem o esquema canônico do
doc 126 §18, possuem identificadores únicos, estão registradas no
manifest do corpus e só referenciam documentos/relatórios reais.
"""

from __future__ import annotations

import re
from pathlib import Path

from controllership_finance_app.application.clara.corpus_manifest import (
    ALL_RIDS,
    AUTHORIZED_SOURCES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FICHAS_DIR = (
    REPO_ROOT
    / "docs/12-roadmap-e-evolucao/controllership-finance/fichas"
)

REQUIRED_SECTIONS = (
    "## Identificação",
    "## Governança",
)

EVIDENCE_MARKERS = (
    "PROVEN",
    "TO_INVENTORY",
    "PLANNED",
    "TARGET",
)

IMPLEMENTATION_STATES = (
    "IMPLEMENTED",
    "OPERATIONAL_VIEW",
    "TARGET_ONLY",
    "SOURCE_UNAVAILABLE",
    "NOT_IMPLEMENTED",
)

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _ficha_path(rid: str) -> Path:
    return FICHAS_DIR / f"{rid}-ficha.md"


def test_all_15_fichas_exist():
    missing = [rid for rid in ALL_RIDS if not _ficha_path(rid).is_file()]
    assert not missing, f"fichas ausentes: {missing}"


def test_fichas_have_canonical_structure():
    for rid in ALL_RIDS:
        text = _ficha_path(rid).read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            assert section in text, f"{rid}: seção ausente {section}"
        assert "Versão da ficha" in text, f"{rid}: sem versão"
        assert any(s in text for s in IMPLEMENTATION_STATES), (
            f"{rid}: sem estado de implementação declarado"
        )


def test_fichas_use_evidence_classification():
    """Toda ficha deve classificar afirmações com o vocabulário de
    evidência — uma ficha sem nenhum marcador é suspeita."""
    for rid in ALL_RIDS:
        text = _ficha_path(rid).read_text(encoding="utf-8")
        assert any(m in text for m in EVIDENCE_MARKERS), (
            f"{rid}: sem classificação de evidência"
        )


def test_fichas_registered_in_corpus_manifest():
    by_id = {s.source_id: s for s in AUTHORIZED_SOURCES}
    for rid in ALL_RIDS:
        source_id = f"ficha-{rid.lower()}"
        spec = by_id.get(source_id)
        assert spec is not None, f"{source_id} ausente do manifest"
        assert spec.path.endswith(f"fichas/{rid}-ficha.md")
        assert spec.related_report_ids == (rid,)


def test_ficha_source_paths_exist_and_unique():
    ficha_specs = [
        s for s in AUTHORIZED_SOURCES if s.source_id.startswith("ficha-")
    ]
    assert len(ficha_specs) == 32  # R01–R15 + índice + processo + AE-00–AE-14
    paths = [s.path for s in ficha_specs]
    assert len(paths) == len(set(paths))
    missing = [p for p in paths if not (REPO_ROOT / p).is_file()]
    assert not missing, f"fontes de ficha ausentes no HEAD: {missing}"


def test_ficha_internal_links_resolve():
    """Links relativos markdown dentro das fichas devem existir."""
    for rid in ALL_RIDS:
        ficha = _ficha_path(rid)
        text = ficha.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (ficha.parent / target.split("#")[0]).resolve()
            assert resolved.is_file(), (
                f"{rid}: link quebrado {target}"
            )


def test_fichas_only_reference_canonical_report_ids():
    rid_re = re.compile(r"\bR\d{2}\b")
    valid = set(ALL_RIDS)
    for rid in ALL_RIDS:
        text = _ficha_path(rid).read_text(encoding="utf-8")
        invalid = {r for r in rid_re.findall(text) if r not in valid}
        assert not invalid, f"{rid}: report_id fora de R01–R15: {invalid}"


def test_not_implemented_reports_are_honest():
    """Honestidade de capability por natureza do relatório:

    - R04/R09/R12/R15 são IMPLEMENTED/visão de acompanhamento —
      `report_not_implemented` só pode aparecer como registro
      histórico superado, nunca como estado vigente;
    - R13/R14 seguem `SOURCE_UNAVAILABLE` (fonte externa) e não
      podem declarar capability de consulta de dados.
    """
    for rid in ("R04", "R09", "R12", "R15"):
        text = _ficha_path(rid).read_text(encoding="utf-8")
        assert "IMPLEMENTED" in text, (
            f"{rid}: ficha deve declarar estado implementado"
        )
        impl = text.split("## Interpretação")[0]
        assert "report_not_implemented" not in impl or (
            "SUPERAD" in impl.upper() or "HISTÓRIC" in impl.upper()
            or "superad" in impl.lower()
        ), f"{rid}: report_not_implemented declarado como vigente"
    for rid in ("R13", "R14"):
        text = _ficha_path(rid).read_text(encoding="utf-8")
        assert "SOURCE_UNAVAILABLE" in text or "nenhuma" in text, (
            f"{rid}: ficha deve declarar ausência de contrato"
        )
