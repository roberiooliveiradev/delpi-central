"""Casos T1–T15 — Playbook 03 especialista em textos."""

from __future__ import annotations

TEXT_SPECIALIST_REGRESSION_CASES: list[dict] = [
    {"id": "T1", "message": "corrija este texto: o produto esta bloqueado", "pure": True, "category": "correct"},
    {"id": "T2", "message": "reescreva de forma mais formal: segue o aviso", "pure": True, "category": "rewrite"},
    {"id": "T3", "message": "traduza para inglês: bom dia equipe", "pure": True, "category": "translate"},
    {"id": "T4", "message": "resuma em tópicos o texto abaixo", "pure": True, "category": "summarize"},
    {"id": "T5", "message": "escreva um e-mail para o fornecedor", "pure": True, "category": "email"},
    {"id": "T6", "message": "transforme em ata estas anotações", "pure": True, "category": "minutes"},
    {"id": "T7", "message": "transforme em checklist as ações", "pure": True, "category": "structure"},
    {"id": "T8", "message": "corrija: produto 10080001 esta bloqueado", "pure": True, "preserved": "10080001"},
    {"id": "T9", "message": "só corrija sem explicar: texto com erro", "pure": True, "final_only": True},
    {
        "id": "T10",
        "message": "consulte o estoque do produto 10080001 e escreva um e-mail",
        "pure": False,
        "mixed": True,
    },
    {"id": "T11", "message": "crie um comunicado interno sobre a manutenção", "pure": True, "category": "announcement"},
    {"id": "T12", "message": "simplifique este texto técnico da BOM", "pure": True, "category": "simplify"},
    {"id": "T13", "message": "compare essas duas versões do parágrafo", "pure": True, "category": "compare"},
    {
        "id": "T14",
        "message": "resuma em tópicos o texto do anexo",
        "pure": True,
        "category": "summarize",
        "attachment_ids": ["att-1"],
        "route_intents": {"text_task", "attachment_task"},
    },
    {"id": "T15", "message": "corrija o texto da lousa", "pure": True, "category": "correct"},
]
