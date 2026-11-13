"""Manifest de fontes do corpus CLARA — domínio Lançamento de Notas Fiscais.

Inventário explícito (F7-R4). Paths relativos à raiz do monorepo
(``--docs-root`` = repo root). Classificações honestas:

- CURRENT_IMPLEMENTATION / APPROVED_RULE — contrato vigente / ADR
- TARGET / TO_INVENTORY — roadmap/plano (não PROVEN de runtime)
- OWNER_REPORTED_VIA_PO — especificação funcional do produto
"""

from __future__ import annotations

from controllership_finance_app.application.clara.corpus_ingestion import (
    SourceSpec,
)

_DOMAIN = "lancamento-notas-fiscais"


def _s(
    source_id: str,
    path: str,
    source_type: str,
    name: str,
    classification: str,
    topic: str,
    *,
    authority: str = "OWNER",
    scope: str = "PORTAL_ACCESS",
) -> SourceSpec:
    return SourceSpec(
        source_id=source_id,
        path=path,
        source_type=source_type,
        name=name,
        origin_authority=authority,
        evidence_classification=classification,
        topic=topic,
        access_scope=scope,
        domain_scope=_DOMAIN,
    )


LNF_AUTHORIZED_SOURCES: list[SourceSpec] = [
    _s(
        "lnf-api-doc",
        "api-delpi/docs/api/lancamento-notas-fiscais.md",
        "DOCUMENT",
        "API Lançamento de Notas Fiscais (contrato api-delpi / referência)",
        "CURRENT_IMPLEMENTATION",
        "lnf-api-contrato",
    ),
    _s(
        "lnf-espec-funcional",
        "docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/especificacao-funcional-tecnica.md",
        "DOCUMENT",
        "Especificação funcional e técnica LNF",
        "OWNER_REPORTED_VIA_PO",
        "lnf-especificacao",
    ),
    _s(
        "lnf-readme",
        "docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/README.md",
        "DOCUMENT",
        "README Lançamento de Notas Fiscais",
        "OWNER_REPORTED_VIA_PO",
        "lnf-overview",
    ),
    _s(
        "lnf-playbook",
        "docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/PLAYBOOK.md",
        "DOCUMENT",
        "Playbook operacional LNF",
        "TO_INVENTORY",
        "lnf-playbook",
    ),
    _s(
        "lnf-roadmap",
        "docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/ROADMAP.md",
        "DOCUMENT",
        "Roadmap LNF",
        "TARGET",
        "lnf-roadmap",
    ),
    _s(
        "lnf-adr-001",
        "docs/12-roadmap-e-evolucao/controllership-finance/adr/ADR-001-hospedagem-lancamento-notas-fiscais.md",
        "CONTRACT",
        "ADR-001 — hospedagem LNF na BFF Controladoria",
        "APPROVED_RULE",
        "lnf-adr-hospedagem",
    ),
    _s(
        "lnf-doc-163",
        "docs/12-roadmap-e-evolucao/controllership-finance/163-plano-migracao-lancamento-notas-fiscais.md",
        "DOCUMENT",
        "Plano de migração LNF → BFF",
        "TARGET",
        "lnf-migracao-plano",
    ),
    _s(
        "lnf-doc-164",
        "docs/12-roadmap-e-evolucao/controllership-finance/164-runbook-corte-lancamento-notas-fiscais.md",
        "DOCUMENT",
        "Runbook de corte LNF",
        "CURRENT_IMPLEMENTATION",
        "lnf-runbook-corte",
    ),
    _s(
        "lnf-doc-165",
        "docs/12-roadmap-e-evolucao/controllership-finance/165-trilha-execucao-migracao-lnf-ate-clara.md",
        "DOCUMENT",
        "Trilha de execução LNF até a CLARA",
        "CURRENT_IMPLEMENTATION",
        "lnf-trilha-clara",
    ),
    _s(
        "lnf-doc-166",
        "docs/12-roadmap-e-evolucao/controllership-finance/166-clara-lancamento-notas-fiscais-contrato.md",
        "CONTRACT",
        "Contrato CLARA × LNF",
        "APPROVED_RULE",
        "lnf-clara-contrato",
    ),
    _s(
        "lnf-help-tooltips",
        "plugins/lancamento-notas-fiscais/src/content/helpTooltips.ts",
        "CODE_EVIDENCE",
        "Ajuda in-app (tooltips) do MFE LNF",
        "CURRENT_IMPLEMENTATION",
        "lnf-ajuda-mfe",
    ),
]
