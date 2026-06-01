"""Casos I1–I15 — Playbook 07 interatividade."""

from __future__ import annotations

INTERACTIVITY_CASES: list[dict] = [
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
        "expect_disabled_label": "Ver estoque",
    },
    {
        "id": "I14",
        "metadata": {
            "contextChips": [
                {"label": "Produto 10080001", "kind": "product", "value": "10080001"},
            ],
            "contextSnapshot": {
                "summary": "Produto 10080001",
                "lastEntities": {"productCode": "10080001"},
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
            "contextSnapshot": {"lastEntities": {"productCode": "10080001"}},
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
]
