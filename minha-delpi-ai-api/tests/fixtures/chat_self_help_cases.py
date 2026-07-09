"""Casos A1–A12 / H1–H10 — Playbook 04 autoajuda §33."""

from __future__ import annotations

SELF_HELP_CASES: list[dict] = [
    {
        "id": "A1",
        "message": "o que você faz?",
        "expect_capability": True,
        "expect_substrings": ("posso ajudar", "agente", "consult"),
        "expect_chips": True,
    },
    {
        "id": "A2",
        "message": "ajuda sobre estoque",
        "expect_capability": True,
        "expect_substrings": ("estoque", "agente", "produto"),
    },
    {
        "id": "A3",
        "message": "como anexo arquivo?",
        "expect_capability": True,
        "expect_substrings": ("anexo", "arquivo", "clipe", "pdf"),
        "expect_chips": True,
    },
    {
        "id": "A4",
        "message": "como gero gráfico?",
        "expect_capability": True,
        "expect_substrings": ("gráfico", "grafico", "dados"),
        "expect_chips": True,
    },
    {
        "id": "A5",
        "message": "o que mudou?",
        "expect_capability": True,
        "expect_substrings": ("novidade", "versão", "versao", "Pesquisa"),
        "expect_chips": True,
    },
    {
        "id": "A6",
        "message": "você consegue excluir produto?",
        "expect_capability": True,
        "expect_substrings": ("não", "nao", "exclu", "alterar", "apenas consult"),
    },
    {
        "id": "A7",
        "message": "o que você pode fazer?",
        "expect_capability": True,
        "expect_substrings": ("Especialista", "consult"),
        "workspace": {
            "agent": {"name": "Agente Produtos", "category": "produtos"},
            "agentId": "11111111-1111-4111-8111-111111111111",
        },
        "allowed_action_ids": ["act.stock"],
        "action_catalog": [
            {
                "actionId": "act.stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "summary": "Estoque do produto",
            }
        ],
        "expect_context_intro": True,
    },
    {
        "id": "A8",
        "message": "por que não tenho acesso ao estoque?",
        "expect_capability": True,
        "expect_substrings": ("agente", "permiss", "estoque", "action"),
    },
    {
        "id": "A9",
        "message": "ajuda sobre lousa",
        "expect_capability": True,
        "expect_substrings": ("lousa", "canvas", "coloque"),
        "expect_chips": True,
    },
    {
        "id": "A10",
        "message": "ajuda sobre texto",
        "expect_capability": True,
        "expect_substrings": ("texto", "corrij", "traduz", "e-mail", "email"),
    },
    {
        "id": "A11",
        "message": "como faço uma boa pergunta?",
        "expect_capability": False,
        "expect_identity_category": "goodQuestion",
        "expect_substrings": ("três", "tres", "identificador", "formato"),
    },
    {
        "id": "A12",
        "message": "como uso você?",
        "expect_capability": False,
        "expect_identity_category": "usage",
        "expect_substrings": ("três", "tres", "agente", "textos"),
    },
]
