"""Casos H1–H13 — OCR hierárquico de desenhos DELPI (Onda 14).

PDFs reais ficam em ``minha-delpi-ai-api/desenhos/`` (gitignored).
Casos sintéticos (H8–H10) usam ``fixture`` para testes unitários futuros.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DrawingHierarchicalCase:
    id: str
    expected_product_code: str | None
    pdf: str | None = None
    fixture: dict[str, Any] | None = None
    notes: str = ""
    expect_conflict: bool = False
    expect_unresolved: bool = False


DRAWING_HIERARCHICAL_REGRESSION_CASES: tuple[DrawingHierarchicalCase, ...] = (
    DrawingHierarchicalCase(
        id="H1",
        pdf="90262373.pdf",
        expected_product_code="90262373",
        notes="Regressão — já passava no baseline jun/2026.",
    ),
    DrawingHierarchicalCase(
        id="H2",
        pdf="90261040.pdf",
        expected_product_code="90261040",
        notes="BOM não pode vencer (ex.: 10400006).",
    ),
    DrawingHierarchicalCase(
        id="H3",
        pdf="90262511.pdf",
        expected_product_code="90262511",
        notes="Decape no corpo.",
    ),
    DrawingHierarchicalCase(
        id="H4",
        pdf="90264234.pdf",
        expected_product_code="90264234",
        notes="COD:/DES: do cliente ≠ código DELPI.",
    ),
    DrawingHierarchicalCase(
        id="H5a",
        pdf="90264235.pdf",
        expected_product_code="90264235",
        notes="Layout WEG repetido (90264235).",
    ),
    DrawingHierarchicalCase(
        id="H5b",
        pdf="90264236.pdf",
        expected_product_code="90264236",
        notes="Layout WEG repetido (90264236).",
    ),
    DrawingHierarchicalCase(
        id="H5c",
        pdf="90264237.pdf",
        expected_product_code="90264237",
        notes="Layout WEG repetido (90264237).",
    ),
    DrawingHierarchicalCase(
        id="H5d",
        pdf="90264238.pdf",
        expected_product_code="90264238",
        notes="Layout WEG repetido (90264238).",
    ),
    DrawingHierarchicalCase(
        id="H6",
        pdf="90263622.pdf",
        expected_product_code="90263622",
        notes="Gate texto nativo → OCR Tesseract.",
    ),
    DrawingHierarchicalCase(
        id="H7",
        pdf="90263149.pdf",
        expected_product_code="90263149",
        notes="Código só no carimbo parcial.",
    ),
    DrawingHierarchicalCase(
        id="H8",
        pdf=None,
        expected_product_code="50232222",
        fixture={
            "stampText": (
                "CÓDIGO DELPI 50232222\nREV. 01\nCLIENTE WEG\n"
                "CHICOTE DE LIGAÇÃO / 50232222"
            ),
        },
        notes="Intermediário 50xx no carimbo — fixture sintético.",
    ),
    DrawingHierarchicalCase(
        id="H9",
        pdf=None,
        expected_product_code="90264234",
        fixture={
            "stampText": "CÓDIGO DELPI 90264234",
            "messageCode": "90261040",
        },
        expect_conflict=True,
        notes="Carimbo A × mensagem B → conflicts[].",
    ),
    DrawingHierarchicalCase(
        id="H10",
        pdf=None,
        expected_product_code=None,
        fixture={"stampText": "CARIMBO ILEGIVEL XXX"},
        expect_unresolved=True,
        notes="Carimbo ilegível → clarificação.",
    ),
    DrawingHierarchicalCase(
        id="H11",
        pdf="90263655.pdf",
        expected_product_code="90263655",
        notes="Decape + código.",
    ),
    DrawingHierarchicalCase(
        id="H12",
        pdf="90264236.pdf",
        expected_product_code="90264236",
        notes="PDF multipágina / corpo denso.",
    ),
    DrawingHierarchicalCase(
        id="H13a",
        pdf="90264231.pdf",
        expected_product_code="90264231",
        notes="Regressão acertos atuais.",
    ),
    DrawingHierarchicalCase(
        id="H13b",
        pdf="90264233.pdf",
        expected_product_code="90264233",
        notes="Regressão acertos atuais.",
    ),
    DrawingHierarchicalCase(
        id="H14",
        pdf=None,
        expected_product_code="90262008",
        fixture={
            "stampText": (
                "ES EXECUTADO VERIFICADO | LIBERADO | DATA\n"
                "| 20/08/24 04 |\n"
                "90262008 REV.08\n"
            ),
        },
        notes="Revisão interna tabela carimbo — regra revision_cross_check (Fase C).",
    ),
)


def pdf_regression_cases() -> tuple[DrawingHierarchicalCase, ...]:
    return tuple(case for case in DRAWING_HIERARCHICAL_REGRESSION_CASES if case.pdf)


def synthetic_regression_cases() -> tuple[DrawingHierarchicalCase, ...]:
    return tuple(case for case in DRAWING_HIERARCHICAL_REGRESSION_CASES if case.fixture)


def case_ids() -> tuple[str, ...]:
    return tuple(case.id for case in DRAWING_HIERARCHICAL_REGRESSION_CASES)
