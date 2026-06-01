"""Casos E1–E15 — Playbook 06 erros e resultados vazios."""

from __future__ import annotations

ERROR_EMPTY_STATES_CASES: list[dict] = [
    {
        "id": "E1",
        "message": "vendas do produto 10080001",
        "answer": "Não encontrei registros para esse filtro.",
        "tool_calls": [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "statusCode": 200,
                    "path": "/sales",
                    "humanizedSummary": {"linhas": ["Nenhum registro encontrado."]},
                },
            }
        ],
        "expect_type": "empty_result",
    },
    {
        "id": "E2",
        "message": "qual o estoque?",
        "answer": (
            "Claro! Para consultar o **estoque**, informe o **código do produto** "
            "(ex.: 10080099). Exemplo: *estoque do produto 10080099*."
        ),
        "expect_type": "missing_parameter",
    },
    {
        "id": "E4",
        "message": "estoque do produto 1",
        "answer": "Não consegui acessar com as permissões atuais.",
        "tool_calls": [
            {
                "name": "execute_external_action",
                "metadata": {"ok": False, "statusCode": 403, "path": "/stock"},
            }
        ],
        "expect_type": "permission_denied",
    },
    {
        "id": "E5",
        "message": "estoque do produto 10080001",
        "answer": "Não foi possível.",
        "tool_calls": [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": False,
                    "statusCode": 503,
                    "path": "/stock",
                    "error": "service unavailable",
                },
            }
        ],
        "expect_type": "api_unavailable",
    },
    {
        "id": "E8",
        "message": "resuma o anexo",
        "answer": "Ok.",
        "attachments": [{"original_filename": "scan.pdf", "status": "index_failed"}],
        "expect_type": "file_unreadable",
    },
    {
        "id": "E13",
        "message": "cadastro do produto 10080001",
        "answer": "O produto não existe.",
        "tool_calls": [
            {
                "name": "execute_external_action",
                "metadata": {"ok": False, "statusCode": 503, "path": "/products/10080001"},
            }
        ],
        "expect_type": "api_unavailable",
        "expect_api_failed": True,
        "expect_non_existence_flag": False,
    },
    {
        "id": "E14",
        "message": "estoque",
        "answer": "Não encontrei.",
        "expect_type": "empty_result",
        "expect_enriched": True,
    },
]
