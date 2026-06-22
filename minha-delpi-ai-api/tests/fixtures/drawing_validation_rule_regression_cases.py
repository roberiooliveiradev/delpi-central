"""Casos de regressão por regra de validação de desenho — Fase C (desacoplamento skill).

Cada caso nomeia uma **categoria de regra** (``rule_id`` do registry), não só um SKU.
PDFs reais permanecem em ``desenhos/``; payloads sintéticos ficam commitados aqui.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DrawingValidationRuleCase:
    id: str
    rule_id: str
    category: str
    notes: str = ""
    smoke_product_code: str | None = None


def payload_stamp_bom_nested_mp() -> dict[str, Any]:
    return {
        "product": {
            "code": "90262008",
            "type": "PA",
            "unit": "MI",
            "current_revision": "004",
        },
        "structure": {
            "items": [
                {
                    "code": "10090062",
                    "quantity": 1.0,
                    "unit": "PC",
                    "components": [],
                },
                {
                    "code": "10120073",
                    "quantity": 650.0,
                    "unit": "MT",
                    "components": [],
                },
                {
                    "code": "50225424",
                    "description": "CA0,75VDAR-00785/04/06-3800-1000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020007", "quantity": 785.0, "unit": "MT"},
                        {"code": "10080110", "quantity": 1000.0, "unit": "PC"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225425",
                    "description": "CA0,75BRAN-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020043", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225426",
                    "description": "CA0,75VERM-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020006", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225427",
                    "description": "CA0,75AZUL-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020042", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225428",
                    "description": "CA0,75PRET-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020046", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225429",
                    "description": "CA0,75MARR-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020048", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
            ]
        },
        "guide": {
            "items": [
                {
                    "product_code": "90262008",
                    "component_code": "50221605",
                    "component_description": "CA18VDAR-00792/04/06-4700-1000",
                    "bom_level": 0,
                },
                {
                    "product_code": "90262008",
                    "component_code": "50221606",
                    "component_description": "CA18BRAN-00792/04/14-3800-0000",
                    "bom_level": 0,
                },
            ]
        },
    }


def pdf_extract_stamp_bom_nested_mp() -> dict[str, Any]:
    return {
        "productCode": "90262008",
        "legible": True,
        "componentCodes": [
            "10020006",
            "10020007",
            "10020042",
            "10020043",
            "10020046",
            "10020048",
            "10080110",
            "10080138",
            "10120073",
        ],
        "intermediateCodes": [],
        "bomRows": [
            {"code": "10120073", "quantity": "12"},
            {"code": "10020007", "quantity": None},
            {"code": "10080110", "quantity": None},
            {"code": "10080138", "quantity": None},
            {"code": "10020043", "quantity": None},
            {"code": "10020006", "quantity": None},
            {"code": "10020042", "quantity": None},
            {"code": "10020046", "quantity": None},
            {"code": "10020048", "quantity": None},
            {"code": "10432635", "quantity": "855", "description": "REV: 08"},
        ],
        "validationScopes": {
            "bom": {
                "sourceKey": "stamp_bom_table",
                "available": True,
                "charCount": 1925,
            },
            "dimensions": {
                "sourceKey": "dimensions_region",
                "available": True,
                "charCount": 1805,
            },
        },
        "sourceMetadata": {
            "stampText": (
                "90262008 REV.08\n"
                "10090062 CONECTOR RETO 6 VIAS NU MACHO UL 94V-2\n"
                "10120073 TUBO ISOLANTE 12,00X0,80\n"
            ),
        },
        "dimensions": {
            "leftDecapeMm": 14.0,
            "rightDecapeMm": None,
            "segmentLengthsMm": [650.0, 792.0, 785.0],
            "cotaDecapeValuesMm": [14.0],
            "decapeIndication": {"left": True, "right": False},
        },
    }


DRAWING_VALIDATION_RULE_CASES: tuple[DrawingValidationRuleCase, ...] = (
    DrawingValidationRuleCase(
        id="R-revision-internal-table",
        rule_id="revision_cross_check",
        category="Revisão interna tabela carimbo × current_revision",
        notes="Captura 04 em linha data+interna; smoke 90262008.",
        smoke_product_code="90262008",
    ),
    DrawingValidationRuleCase(
        id="R-structure-bom-validity",
        rule_id="structure_bom_validity",
        category="Vigência SG1010 e revisão PDF × cadastro",
        notes="bom_validity.current + aviso quando revisão PDF < current_revision.",
        smoke_product_code="90262008",
    ),
    DrawingValidationRuleCase(
        id="R-bom-stamp-nested-mp",
        rule_id="bom_comparison",
        category="BOM carimbo — MP aninhado não vira extra",
        smoke_product_code="90262008",
    ),
    DrawingValidationRuleCase(
        id="R-bom-root-mp-haystack",
        rule_id="bom_comparison",
        category="MP raiz encontrado no haystack do carimbo",
        smoke_product_code="90262008",
    ),
    DrawingValidationRuleCase(
        id="R-guide-legacy-pi-fingerprint",
        rule_id="guide_component",
        category="Roteiro × PI legado por fingerprint de cabo",
        smoke_product_code="90262008",
    ),
    DrawingValidationRuleCase(
        id="R-decape-global-misassigned",
        rule_id="decape_per_intermediate",
        category="Decape global 14 mm não gera mismatch por intermediário",
        smoke_product_code="90262008",
    ),
    DrawingValidationRuleCase(
        id="R-quantity-from-description",
        rule_id="bom_quantity",
        category="Quantidade tubo da descrição (12) não é confiável",
        smoke_product_code="90262008",
    ),
    DrawingValidationRuleCase(
        id="R-segment-structure-piece-qty",
        rule_id="segment_length",
        category="Cota 650 mm coincide com consumo MT normalizado — não pendência falsa",
        smoke_product_code="90262008",
    ),
    DrawingValidationRuleCase(
        id="R-bom-quantity-tolerance",
        rule_id="bom_quantity",
        category="Quantidade dentro da tolerância ±10%",
    ),
    DrawingValidationRuleCase(
        id="R-guide-component-structure",
        rule_id="guide_component",
        category="component_code fora da estrutura do PI",
    ),
    DrawingValidationRuleCase(
        id="R-balloon-structured-bom",
        rule_id="balloon_presence",
        category="BOM colunar satisfaz presença sem anotações",
    ),
    DrawingValidationRuleCase(
        id="R-registry-7026-balloon",
        rule_id="balloon_presence",
        category="Família 7026 desliga balloon_presence",
    ),
    DrawingValidationRuleCase(
        id="R-product-code-mismatch",
        rule_id="product_code_cross_check",
        category="Código PDF diverge do cadastro SB1010",
    ),
    DrawingValidationRuleCase(
        id="R-guide-structure-extra",
        rule_id="guide_structure",
        category="Produto do roteiro fora da estrutura SG1010",
    ),
    DrawingValidationRuleCase(
        id="R-multipage-low-coverage",
        rule_id="multipage_coverage",
        category="BOM multipágina com cobertura baixa",
    ),
    DrawingValidationRuleCase(
        id="R-intermediate-missing",
        rule_id="intermediate_presence",
        category="Intermediário 50xx ausente no PDF",
    ),
    DrawingValidationRuleCase(
        id="R-intermediate-length",
        rule_id="intermediate_length",
        category="Comprimento 50xx × cabo filho fora de tolerância",
    ),
    DrawingValidationRuleCase(
        id="R-total-length",
        rule_id="total_length",
        category="Comprimento total PDF × referência estrutura",
    ),
    DrawingValidationRuleCase(
        id="R-decapes-ed",
        rule_id="decapes_ed",
        category="Decapes E/D globais no PDF",
    ),
    DrawingValidationRuleCase(
        id="R-dimension-note-ambiguous",
        rule_id="dimension_note",
        category="Nota dimensional ambígua (termo vs decape)",
    ),
)


def rule_ids_with_cases() -> frozenset[str]:
    return frozenset(case.rule_id for case in DRAWING_VALIDATION_RULE_CASES)


def cases_for_rule(rule_id: str) -> tuple[DrawingValidationRuleCase, ...]:
    normalized = str(rule_id or "").strip()

    return tuple(
        case for case in DRAWING_VALIDATION_RULE_CASES if case.rule_id == normalized
    )
