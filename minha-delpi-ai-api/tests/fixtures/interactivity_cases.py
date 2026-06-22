"""Casos I1–I15 — Playbook 07 interatividade."""

from __future__ import annotations

INTERACTIVITY_CASES: list[dict] = [
    {
        "id": "I2",
        "metadata": {
            "followUpSuggestions": [
                {"label": "Ver fornecedores", "query": "fornecedores"},
                {"label": "Gerar gráfico", "query": "gráfico de estoque"},
            ],
            "followUpOutcome": "stock",
        },
        "expect_in_suggestions": "Ver fornecedores",
    },
    {
        "id": "I4",
        "metadata": {
            "emailFollowUpSuggestions": [
                {"label": "Deixar mais formal", "query": "deixe o e-mail mais formal"},
                {"label": "Tom mais executivo", "query": "tom mais executivo"},
            ],
        },
        "expect_group": "formatar",
    },
    {
        "id": "I1",
        "metadata": {
            "followUpSuggestions": [
                {"label": "Ver estoque", "query": "estoque do produto {{productCode}}"},
                {"label": "Ver fornecedores", "query": "fornecedores do produto {{productCode}}"},
            ],
            "followUpOutcome": "product",
        },
        "expect_primary_labels": ("Ver estoque",),
    },
    {
        "id": "I3",
        "metadata": {
            "textCorrectionFollowUpSuggestions": [
                {"label": "Deixar mais formal", "query": "deixe mais formal"},
                {"label": "Colocar na lousa", "query": "coloque na lousa"},
            ],
        },
        "expect_group": "formatar",
    },
    {
        "id": "I5",
        "metadata": {
            "errorRecoveryFollowUpSuggestions": [
                {"label": "Tentar novamente", "query": "tente novamente"},
            ],
            "errorHandling": {"type": "empty_result"},
        },
        "expect_group": "recuperar",
    },
    {
        "id": "I10",
        "metadata": {
            "attachmentFollowUpSuggestions": [
                {"label": "Resumir", "query": "resuma o anexo"},
                {"label": "Colocar na lousa", "query": "coloque na lousa"},
            ],
        },
        "expect_in_suggestions": "Resumir",
    },
    {
        "id": "I11",
        "metadata": {
            "followUpSuggestions": [
                {"label": f"Chip {index}", "query": f"query {index}"}
                for index in range(8)
            ],
        },
        "expect_more": True,
    },
    {
        "id": "I7",
        "tool_calls": [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "presentation": {"type": "table", "title": "Produtos"},
                },
            }
        ],
        "expect_presentation_label": "Exportar CSV",
    },
    {
        "id": "I8",
        "tool_calls": [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "presentation": {"type": "chart", "title": "Vendas"},
                },
            }
        ],
        "expect_presentation_label": "Ver como tabela",
    },
    {
        "id": "I9",
        "metadata": {
            "canvasFollowUpSuggestions": [
                {"label": "Corrigir", "query": "corrija o texto da lousa"},
                {"label": "Resumir", "query": "resuma a lousa"},
            ],
        },
        "expect_in_suggestions": "Corrigir",
    },
    {
        "id": "I6",
        "tool_calls": [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "presentation": {"type": "table", "title": "Vendas"},
                },
            }
        ],
        "expect_presentation": True,
    },
    {
        "id": "I12",
        "metadata": {
            "canvasFollowUpSuggestions": [
                {"label": "Limpar lousa", "query": "limpe a lousa atual"},
            ],
        },
        "expect_requires_confirmation": True,
    },
    {
        "id": "I13",
        "metadata": {
            "followUpSuggestions": [
                {"label": "Ver estoque", "query": "estoque do produto 1"},
            ],
        },
        "workspace_context": {"capabilities": {"canvas": True}, "userActivatedAgent": False},
        "expect_absent_label": "Ver estoque",
    },
    {
        "id": "I14",
        "metadata": {
            "contextChips": [
                {"label": "Produto 10080001", "kind": "product", "value": "10080001"},
            ],
            "contextSnapshot": {
                "summary": "Produto 10080001",
                "operationalFocus": {"productCode": "10080001"},
            },
            "followUpSuggestions": [
                {"label": "Ver fornecedores", "query": "fornecedores"},
            ],
        },
        "expect_context_bar": True,
    },
    {
        "id": "I15",
        "metadata": {
            "followUpSuggestions": [
                {
                    "label": "Ver estoque",
                    "query": "Qual o estoque do produto {{productCode}}?",
                },
            ],
            "contextSnapshot": {"operationalFocus": {"productCode": "10080001"}},
        },
        "expect_resolved_query": "10080001",
    },
    {
        "id": "I16",
        "metadata": {
            "followUpSuggestions": [
                {"label": "Colocar na lousa", "query": "coloque na lousa"},
                {"label": "Ver estoque", "query": "estoque"},
            ],
        },
        "workspace_context": {
            "capabilities": {"canvas": True},
            "userActivatedAgent": True,
            "workingMemory": {
                "behaviorInstructions": {
                    "interactivityUsage": '{"Colocar na lousa": 5}',
                },
            },
        },
        "expect_primary_label": "Colocar na lousa",
    },
    {
        "id": "I17",
        "metadata": {
            "followUpSuggestions": [
                {"label": "Consultar produto", "query": "me fale do produto 1"},
                {"label": "Ver estoque", "query": "estoque do produto 1"},
                {"label": "Gerar gráfico", "query": "gere um gráfico"},
                {"label": "Pesquisar na web", "query": "pesquise na web sobre tendências"},
            ],
        },
        "workspace_context": {
            "capabilities": {"canvas": True},
            "userActivatedAgent": False,
            "actionsEnabled": False,
        },
        "expect_absent_labels": ["Consultar produto", "Ver estoque", "Gerar gráfico"],
        "expect_in_suggestions": "Pesquisar na web",
    },
]
