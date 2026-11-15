"""Fichas TES-00..TES-05 — conhecimento da CLARA sobre o cadastro de TES (SF4).

Garante registro no corpus, estrutura canônica, segmentação sem corte,
catálogo completo frente à extração da SF4 e catálogo reprodutível pelo
gerador versionado.
"""

from __future__ import annotations

import csv
import importlib.util
import re
from pathlib import Path

from controllership_finance_app.application.clara.corpus_ingestion import segment_markdown
from controllership_finance_app.application.clara.corpus_manifest import (
    AUTHORIZED_SOURCES,
    OPERATIONAL_SOURCE_IDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TES_DIR = REPO_ROOT / "docs/12-roadmap-e-evolucao/controllership-finance/fichas/tes"
SOURCE_CSV = TES_DIR / "fonte" / "sf4-2026-11-09.csv"
GENERATOR = TES_DIR / "fonte" / "gerar_catalogo_tes.py"
TES_IDS = [f"ficha-tes-{n:02d}" for n in range(6)]
R10_EXCLUDED = ("001", "003", "016", "020", "030", "040", "080", "083", "085",
                "120", "159", "204", "318")


def _rows() -> list[dict]:
    with SOURCE_CSV.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def _text(n: int) -> str:
    return (TES_DIR / f"TES-{n:02d}.md").read_text(encoding="utf-8")


def test_tes_fichas_registered_as_operational_sources():
    by_id = {s.source_id: s for s in AUTHORIZED_SOURCES}
    for source_id in TES_IDS:
        spec = by_id[source_id]
        assert source_id in OPERATIONAL_SOURCE_IDS
        assert spec.access_scope == "PORTAL_ACCESS"
        assert spec.domain_scope == "controllership"
        assert spec.topic == "tes"
        assert (REPO_ROOT / spec.path).is_file(), spec.path


def test_tes_fichas_structure_and_naming():
    for n in range(6):
        text = _text(n)
        assert text.startswith(f"# TES-{n:02d} — ")
        for section in ("## Identificação", "## Governança", "Versão da ficha"):
            assert section in text, (n, section)
        assert "IMPLEMENTED" in text
        # Usuário vê o nome do processo, não o código do Transformômetro.
        assert "PROC-0072" not in text


def test_tes_segments_fit_without_cut():
    for n in range(6):
        for segment in segment_markdown(_text(n)):
            assert "#part-" not in segment.heading_path, (n, segment.heading_path)
            assert len(segment.content) <= 6000


def test_catalog_lists_every_tes_of_the_extraction():
    rows = _rows()
    assert len(rows) == 458
    entry, exit_ = _text(3), _text(4)
    for row in rows:
        target = entry if row["tipo"] == "Entrada" else exit_
        assert re.search(rf"^\| TES {re.escape(row['codigo'])} \|", target, re.M), row["codigo"]
    assert sum(r["bloqueado"] != "Sim" for r in rows) == 234


def test_catalog_is_reproducible_from_generator():
    spec = importlib.util.spec_from_file_location("gerar_catalogo_tes", GENERATOR)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    rows = _rows()
    entry = gen.render([r for r in rows if r["tipo"] == "Entrada"], side="Entrada",
                       code="TES-03", data_extracao="09/11/2026")
    exit_ = gen.render([r for r in rows if r["tipo"] == "Saida"], side="Saida",
                       code="TES-04", data_extracao="09/11/2026")
    assert entry == _text(3)
    assert exit_ == _text(4)


def test_key_facts_are_present():
    matrix = _text(1)
    for code in R10_EXCLUDED:
        assert re.search(rf"^\| {code} \|.*\| R10 \|", matrix, re.M), code
    assert "TO_INVENTORY (LISTA-13)" in matrix
    assert "F4_ESTOQUE='S'" in matrix and "F4_DUPLIC='S'" in matrix
    concept = _text(0)
    assert "499 e 999 do R07 (ajustes de inventário) são tipos de movimento da SD3" in concept
    assert "001 a 500 = entrada; 501 a 999 = saída" in concept
    pend = _text(5)
    for item in ("P-TES-01", "P-TES-02", "P-TES-03"):
        assert item in pend
