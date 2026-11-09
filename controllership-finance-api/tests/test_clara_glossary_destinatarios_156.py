"""Cobertura mínima do glossário doc 156 na superfície operacional.

Gate 085: a recuperação produtiva da CLARA usa as fichas
PORTAL_ACCESS. O Documento 156 fica no manifesto como APPROVED_RULE
(auditoria/proveniência) e o conteúdo operacional entra pela ficha
do processo + alinhamento R01/R02/R03/R13 — sem duplicar a fonte
operacional.
"""

from __future__ import annotations

import re
from pathlib import Path

from controllership_finance_app.application.clara.corpus_ingestion import (
    segment_markdown,
)
from controllership_finance_app.application.clara.corpus_manifest import (
    AUTHORIZED_SOURCES,
    OPERATIONAL_SOURCE_IDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Dez perguntas obrigatórias do brief — markers que precisam existir
# em segmentos operacionais citáveis (ficha-processo e irmãos).
GLOSSARY_CASES = (
    dict(
        id="G156-Q1",
        q="Quem é responsável pelo fechamento mensal da DELPI?",
        cite=("ficha-processo",),
        markers=("Controladoria interna", "prepara"),
    ),
    dict(
        id="G156-Q2",
        q="Qual é a diferença entre Financeiro e Controladoria?",
        cite=("ficha-processo",),
        markers=("Financeiro", "origem", "Controladoria interna"),
    ),
    dict(
        id="G156-Q3",
        q="Qual é a diferença entre Contabilidade externa e Fiscal?",
        cite=("ficha-processo",),
        markers=("Contabilidade externa", "FISCAL", "entregas fiscais"),
    ),
    dict(
        id="G156-Q4",
        q="O que significa DRE no contexto do Portal?",
        cite=("ficha-processo",),
        markers=("Demonstração do Resultado", "apelido", "público externo"),
    ),
    dict(
        id="G156-Q5",
        q="Quem prepara os documentos e quem os recebe?",
        cite=("ficha-processo",),
        markers=("prepara", "Controladoria interna", "Contabilidade externa"),
    ),
    dict(
        id="G156-Q6",
        q="Por que os 14 itens possuem recipient_area=CONTABIL?",
        cite=("ficha-processo",),
        markers=("14 itens", "recipient_area=CONTABIL", "Contabilidade externa"),
    ),
    dict(
        id="G156-Q7",
        q="A permissão access.dre permite consultar qualquer documento?",
        cite=("ficha-processo",),
        markers=("access.dre", "não", "irrestrito"),
    ),
    dict(
        id="G156-Q8",
        q="O relatório P7 deve ser entregue consolidado ou por filial?",
        cite=("ficha-processo", "ficha-r03"),
        markers=("P7", "por filial"),
    ),
    dict(
        id="G156-Q9",
        q="Os relatórios financeiros são consolidados?",
        cite=("ficha-processo", "ficha-r01", "ficha-r02"),
        markers=("financeiro", "consolidado"),
    ),
    dict(
        id="G156-Q10",
        q="Natureza fiscal implica destinatário FISCAL?",
        cite=("ficha-processo", "ficha-r03"),
        markers=("natureza fiscal", "não", "FISCAL"),
    ),
)


def _operational_text() -> dict[str, str]:
    out: dict[str, str] = {}
    for spec in AUTHORIZED_SOURCES:
        if spec.source_id not in OPERATIONAL_SOURCE_IDS:
            continue
        body = (REPO_ROOT / spec.path).read_text(encoding="utf-8")
        segments = "\n".join(
            f"{segment.heading_path}\n{segment.content}"
            for segment in segment_markdown(body)
        )
        out[spec.source_id] = f"{body}\n{segments}".lower()
    return out


def test_doc_156_registered_as_approved_rule_not_operational_duplicate():
    by_id = {s.source_id: s for s in AUTHORIZED_SOURCES}
    assert "doc-156" in by_id
    spec = by_id["doc-156"]
    assert spec.evidence_classification == "APPROVED_RULE"
    assert spec.origin_authority == "PO"
    assert "156-glossario" in spec.path
    # Gate 085: não duplicar a superfície operacional — o glossário
    # operacional vive na ficha-processo; doc-156 permanece auditoria.
    assert "doc-156" not in OPERATIONAL_SOURCE_IDS
    assert spec.access_scope == "INTERNAL_ONLY"
    assert (REPO_ROOT / spec.path).is_file()


def test_glossary_ten_questions_have_citable_operational_evidence():
    texts = _operational_text()
    assert "ficha-processo" in texts
    for case in GLOSSARY_CASES:
        found = False
        for source_id in case["cite"]:
            haystack = texts[source_id]
            if all(
                re.search(
                    r"(?<!\w)" + re.escape(marker.lower()) + r"(?!\w)",
                    haystack,
                )
                for marker in case["markers"]
            ):
                found = True
                break
        assert found, (case["id"], case["q"], case["markers"])


def test_glossary_does_not_claim_dre_is_recipient_area_or_unrestricted():
    process = _operational_text()["ficha-processo"]
    assert "recipient_area" in process
    assert "access.dre" in process
    assert "irrestrito" in process
    assert "departamento formal" in process or "não é módulo" in process
    # Negativos: não afirmar que DRE é área recipient_area.
    assert "recipient_area=dre" not in process
    assert "recipient_area = dre" not in process
