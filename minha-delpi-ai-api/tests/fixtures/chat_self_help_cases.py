"""Casos H1–H10 — playbook autoajuda §25."""

from __future__ import annotations

SELF_HELP_CASES: list[dict] = [
    {
        "id": "H1",
        "message": "o que você pode fazer?",
        "expect_capability": True,
        "expect_substrings": ("posso ajudar", "agente", "consult"),
    },
    {
        "id": "H2",
        "message": "como consulto estoque?",
        "expect_capability": True,
        "expect_substrings": ("estoque", "agente", "produto"),
    },
    {
        "id": "H3",
        "message": "como faço gráfico?",
        "expect_capability": True,
        "expect_substrings": ("gráfico", "grafico", "dados"),
    },
    {
        "id": "H4",
        "message": "você consegue excluir produto?",
        "expect_capability": True,
        "expect_substrings": ("não", "nao", "exclu", "alterar", "apenas consult"),
    },
    {
        "id": "H5",
        "message": "o que mudou?",
        "expect_capability": True,
        "expect_substrings": ("novidade", "versão", "versao", "Pesquisa"),
    },
    {
        "id": "H6",
        "message": "o que você consegue consultar?",
        "expect_capability": True,
        "expect_substrings": ("consult", "agente", "API", "action"),
        "workspace": {"agent": {"name": "Agente Teste"}, "agentId": "11111111-1111-4111-8111-111111111111"},
        "allowed_action_ids": ["act.stock"],
        "action_catalog": [
            {
                "actionId": "act.stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "summary": "Estoque do produto",
            }
        ],
    },
    {
        "id": "H7",
        "message": "você corrige textos?",
        "expect_capability": True,
        "expect_substrings": ("texto", "corrij", "formal", "traduz"),
    },
    {
        "id": "H8",
        "message": "como uso pesquisa web?",
        "expect_capability": True,
        "expect_substrings": ("web", "internet", "pesquis"),
    },
    {
        "id": "H9",
        "message": "como uso a lousa?",
        "expect_capability": True,
        "expect_substrings": ("lousa", "canvas", "coloque"),
    },
    {
        "id": "H10",
        "message": "por que não consigo consultar estoque?",
        "expect_capability": True,
        "expect_substrings": ("agente", "permiss", "estoque", "action"),
    },
]
