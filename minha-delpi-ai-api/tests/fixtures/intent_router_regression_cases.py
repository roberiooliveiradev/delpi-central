"""Casos de regressão R1–R15 — Playbook 02 roteamento de intenção."""

from __future__ import annotations

from typing import Any

INTENT_ROUTER_REGRESSION_CASES: list[dict[str, Any]] = [
    {
        "id": "R1",
        "message": "Corrija este texto",
        "expected_intent": "text_task",
        "expected_sub_intent": "correct",
    },
    {
        "id": "R2",
        "message": "Estoque do produto 10080001",
        "expected_intent": "operational_query",
        "expected_sub_intent": "stock_lookup",
    },
    {
        "id": "R3",
        "message": "O que você pode fazer?",
        "expected_intent": "self_help",
    },
    {
        "id": "R4",
        "message": "Pesquise na web sobre WEG",
        "expected_intent": "web_search",
        "requires_web": True,
    },
    {
        "id": "R5",
        "message": "Coloque isso na lousa",
        "expected_intent": "canvas_task",
        "requires_canvas": True,
    },
    {
        "id": "R6",
        "message": "Agora fornecedores",
        "expected_intent": "operational_query",
        "expected_sub_intent": "supplier_lookup",
        "is_follow_up": True,
        "history": [
            {"role": "user", "content": "me fale do produto 10080001"},
            {
                "role": "assistant",
                "content": "Cadastro do produto.",
                "metadata": {
                    "toolCalls": [
                        {
                            "name": "execute_external_action",
                            "metadata": {"ok": True, "path": "/products/10080001/analyser"},
                        }
                    ]
                },
            },
        ],
        "expected_product_code": "10080001",
    },
    {
        "id": "R7",
        "message": "Resuma esse PDF",
        "expected_intent": "attachment_task",
        "attachment_ids": ["att-1"],
    },
    {
        "id": "R8",
        "message": "Monte SQL",
        "expected_intent": "sql_task",
        "expected_sub_intent": "sql_generate",
    },
    {
        "id": "R8b",
        "message": (
            "Monte uma consulta para listar clientes ativos da tabela SA1, "
            "só código e nome, sem executar."
        ),
        "expected_intent": "sql_task",
        "expected_sub_intent": "sql_generate",
        "text_task_pure": False,
    },
    {
        "id": "R9",
        "message": "Quem é você?",
        "expected_intent": "identity",
    },
    {
        "id": "R10",
        "message": "Obrigado",
        "expected_intent": "small_talk",
    },
    {
        "id": "R11",
        "message": "Mostre em gráfico",
        "expected_intent": "presentation_task",
    },
    {
        "id": "R12",
        "message": "Sim",
        "expected_intent": "clarification",
        "history": [
            {
                "role": "assistant",
                "content": "Qual filial deseja consultar?",
                "metadata": {
                    "activePending": {
                        "kind": "branch",
                        "question": "Qual filial deseja consultar?",
                        "options": ["01", "02"],
                    }
                },
            },
        ],
    },
    {
        "id": "R13",
        "message": "Corrija: estoque baixo",
        "expected_intent": "text_task",
        "requires_tool": False,
    },
    {
        "id": "R14",
        "message": "Consulte o estoque do produto 10080001 e escreva um e-mail para compras",
        "expected_intent": "mixed_task",
    },
    {
        "id": "R15",
        "message": "O que diz a norma?",
        "expected_intent": "rag_question",
    },
]
