"""CLARA-PARITY-014 — paridade de conhecimento do corpus.

Garante que as fontes determinadas pela matriz de paridade (doc 121)
permanecem autorizadas no manifest e que o vocabulário de
classificação/proveniência usado pelas fontes novas é o canônico.
"""

from __future__ import annotations

import re
from pathlib import Path

from controllership_finance_app.application.clara.corpus_manifest import (
    ALL_RIDS,
    AUTHORIZED_SOURCES,
)

REQUIRED_PARITY_SOURCE_IDS = {
    "doc-49",
    "doc-91",
    "doc-115",
    "doc-116",
    "doc-117",
    "doc-118",
    "doc-119",
    "doc-120",
    "doc-121",
}

VALID_CLASSIFICATIONS = {
    "OWNER_REPORTED_VIA_PO",
    "APPROVED_RULE",
    "TARGET",
    "CURRENT_IMPLEMENTATION",
    "TO_INVENTORY",
}

REPO_ROOT = Path(__file__).resolve().parents[2]


def _source(source_id: str):
    for spec in AUTHORIZED_SOURCES:
        if spec.source_id == source_id:
            return spec
    raise AssertionError(f"fonte ausente do manifest: {source_id}")


def test_parity_sources_authorized():
    ids = {s.source_id for s in AUTHORIZED_SOURCES}
    missing = REQUIRED_PARITY_SOURCE_IDS - ids
    assert not missing, f"fontes de paridade ausentes: {missing}"


def test_manifest_uses_canonical_classification_vocabulary():
    invalid = {
        s.source_id: s.evidence_classification
        for s in AUTHORIZED_SOURCES
        if s.evidence_classification not in VALID_CLASSIFICATIONS
    }
    assert not invalid, f"classificação fora do vocabulário: {invalid}"


def test_related_report_ids_are_canonical():
    valid = set(ALL_RIDS)
    invalid = {
        s.source_id: tuple(r for r in s.related_report_ids if r not in valid)
        for s in AUTHORIZED_SOURCES
    }
    invalid = {k: v for k, v in invalid.items() if v}
    assert not invalid, f"report_id fora de R01–R15: {invalid}"


def test_parity_matrix_doc_defines_required_sections():
    doc = REPO_ROOT / "docs/12-roadmap-e-evolucao/controllership-finance/121-clara-paridade-portal-matriz-cp-2026-10-29.md"  # noqa: E501
    text = doc.read_text(encoding="utf-8")
    for needle in (
        "PARITY_PASS",
        "READ_TOOL_GAP",
        "NOT_APPLICABLE",
        "IDENTITY_ONLY",
        "PLANNED",
        "access.dre",
        "closing/monthly-closing",
        "R01",
        "R15",
    ):
        assert needle in text, f"seção/termo obrigatório ausente: {needle}"


def test_parity_source_paths_exist_and_unique():
    paths = [s.path for s in AUTHORIZED_SOURCES]
    assert len(paths) == len(set(paths))
    missing = [p for p in paths if not (REPO_ROOT / p).is_file()]
    assert not missing, f"fontes ausentes no HEAD: {missing}"


def test_doc121_covers_all_report_ids_and_surfaces():
    doc = REPO_ROOT / "docs/12-roadmap-e-evolucao/controllership-finance/121-clara-paridade-portal-matriz-cp-2026-10-29.md"  # noqa: E501
    text = doc.read_text(encoding="utf-8")
    for rid in ALL_RIDS:
        assert rid in text, f"{rid} ausente da matriz de paridade"
    for view in (
        "closing/financial-settlements",
        "closing/stock-inventory",
        "closing/pendencies",
        "closing/packages",
        "closing/cockpit",
        "closing/documents",
        "closing/my-tasks",
        "closing/admin",
        "profile",
    ):
        assert view in text, f"rota ausente da matriz: {view}"


def test_doc121_references_only_real_routes():
    """Sala de interação, Ajuda dedicada e Visão geral dedicada só
    podem aparecer classificadas como PLANEJADO, nunca como rota."""
    doc = REPO_ROOT / "docs/12-roadmap-e-evolucao/controllership-finance/121-clara-paridade-portal-matriz-cp-2026-10-29.md"  # noqa: E501
    text = doc.read_text(encoding="utf-8")
    for planned in ("Sala de interação", "Ajuda dedicada",
                    "Visão geral **dedicada**"):
        for line in text.splitlines():
            if planned in line:
                assert "PLANEJADO" in line or "PLANNED" in line, (
                    f"superfície futura sem marcação PLANEJADO: {line}"
                )
