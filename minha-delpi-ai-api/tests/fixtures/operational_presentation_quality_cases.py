"""Casos de qualidade de apresentação operacional — perguntas reais jun/2026."""

from __future__ import annotations

from typing import Any

OPERATIONAL_PRESENTATION_QUALITY_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "production_status_situacao",
        "fixture": "product_production_status_90269002.json",
        "path": "/products/90269002/production-status",
        "user_message": "Situação produtiva do 90269002 na data de hoje.",
        "forbidden": [
            "Foram retornados",
            "Situação produtiva do PA e intermediários",
        ],
        "required": [
            "Situação na data",
            "Produção do PA",
            "90269002",
        ],
        "data_answer_required": True,
    },
    {
        "id": "production_status_open_op",
        "fixture": "product_production_status_90269002.json",
        "path": "/products/90269002/production-status",
        "user_message": "O 90269002 tem OP aberta hoje? Já iniciou produção?",
        "forbidden": ["Foram retornados"],
        "required": ["Sim", "Não"],
        "data_answer_required": True,
    },
    {
        "id": "structure_exclusivity_mps",
        "fixture": "product_structure_exclusivity_90261805.json",
        "path": "/products/90261805/structure/exclusivity",
        "user_message": "Quais MPs compõem a estrutura do 90261805? Tem MP exclusiva?",
        "forbidden": ["Foram retornados 4 registros"],
        "required": [
            "Resposta",
            "Matérias-primas",
            "90261805",
        ],
        "data_answer_required": True,
    },
    {
        "id": "structure_exclusivity_verdict",
        "fixture": "product_structure_exclusivity_90261805.json",
        "path": "/products/90261805/structure/exclusivity",
        "user_message": "O produto 90261805 tem matéria-prima exclusiva?",
        "forbidden": ["Foram retornados"],
        "required": ["Não", "exclusiva"],
        "data_answer_required": True,
    },
)
