"""Casos de regressão V1–V8 — Onda 13 (playbook §10)."""

from __future__ import annotations

REGRESSION_CASES: tuple[dict, ...] = (
    {
        "id": "V1",
        "description": "PDF digital com texto nativo legível",
        "native_text": "PRODUTO 90260140 REV.03 CLIENTE ACME " * 5,
        "expect_legible": True,
        "expect_engine_contains": "native",
    },
    {
        "id": "V2",
        "description": "Scan sem texto embutido — OCR necessário",
        "native_text": "",
        "ocr_text": "CODIGO 90260155 REV.04",
        "expect_legible": True,
        "expect_stages_contains": "tesseract",
    },
    {
        "id": "V3",
        "description": "Documento ilegível",
        "native_text": "ab",
        "ocr_text": "",
        "expect_legible": False,
    },
    {
        "id": "V7",
        "description": "Skill desligada — só estágio legado",
        "vision_enabled": False,
        "native_text": "texto curto",
        "expect_unchanged": True,
    },
    {
        "id": "V8",
        "description": "Integração drawing — código no merge",
        "vision_engine": "tesseract",
        "vision_product_code": "90260140",
        "drawing_product_code": None,
        "expect_merged_code": "90260140",
    },
)
