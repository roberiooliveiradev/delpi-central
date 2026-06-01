"""Casos L1–L12 — Playbook 05 anexos e lousa."""

from __future__ import annotations

ATTACHMENTS_CANVAS_CASES: list[dict] = [
    {
        "id": "L1",
        "kind": "welcome",
        "message": "",
        "attachments": [{"original_filename": "relatorio.pdf", "status": "indexed"}],
        "expect_substrings": ("Arquivo recebido", "resumo", "anexado"),
    },
    {
        "id": "L2",
        "kind": "follow_up",
        "had_attachments": True,
        "expect_labels": ("Resumir", "Colocar na lousa"),
    },
    {
        "id": "L5",
        "kind": "canvas_copy",
        "message": "coloque isso na lousa",
        "previous_messages": [
            {
                "role": "assistant",
                "content": "Resumo do produto 10080001 com estoque disponível.",
                "id": "msg-a1",
            }
        ],
        "expect_open": True,
    },
    {
        "id": "L7",
        "kind": "large_file",
        "attachments": [
            {
                "original_filename": "big.pdf",
                "status": "indexed",
                "metadata": {"preview": {"kind": "document", "charCount": 200000}},
            }
        ],
        "expect_substrings": ("extenso", "resumo geral"),
    },
    {
        "id": "L11",
        "kind": "unreadable",
        "attachments": [{"original_filename": "scan.pdf", "status": "index_failed"}],
        "expect_substrings": ("não consegui ler", "reenviar"),
    },
    {
        "id": "L3",
        "kind": "attachment_to_canvas",
        "message": "resuma o arquivo anexado e coloque o resultado na lousa",
        "previous_messages": [
            {
                "role": "assistant",
                "content": "Resumo do PDF: vendas Q1 estáveis.",
                "metadata": {
                    "attachmentSummaries": [{"filename": "relatorio.pdf", "parsed": True}],
                },
            }
        ],
        "expect_open": True,
    },
    {
        "id": "L4",
        "kind": "canvas_append",
        "message": "acrescente isso na lousa",
        "previous_messages": [
            {
                "role": "assistant",
                "content": "## Base\n\nTexto base.",
                "metadata": {
                    "canvasOpen": {
                        "title": "Base",
                        "markdown": "## Base\n\nTexto base.",
                    }
                },
            },
            {"role": "assistant", "content": "## Novo\n\nSegunda parte."},
        ],
        "expect_open": True,
        "expect_substrings": ("Texto base", "Segunda parte"),
    },
    {
        "id": "L6",
        "kind": "canvas_transform",
        "message": "transforme o conteúdo da lousa em checklist",
        "previous_messages": [
            {
                "role": "assistant",
                "metadata": {
                    "canvasOpen": {
                        "title": "Pendências",
                        "markdown": "Revisar estoque\nEnviar e-mail",
                    }
                },
            }
        ],
        "expect_open": True,
        "expect_markdown_substrings": ("- [ ]",),
    },
    {
        "id": "L9",
        "kind": "canvas_version",
        "expect_version": 4,
    },
    {
        "id": "L10",
        "kind": "source_citation",
        "attachments": [{"original_filename": "contrato.pdf", "status": "indexed"}],
        "answer": "O prazo de entrega é de 30 dias.",
        "expect_citation": True,
    },
    {
        "id": "L12",
        "kind": "canvas_ambiguity",
        "message": "coloque isso na lousa",
        "previous_messages": [
            {
                "role": "assistant",
                "content": "A" * 120,
                "metadata": {
                    "attachmentSummaries": [{"filename": "doc.pdf"}],
                },
            },
            {
                "role": "user",
                "content": "segue anexo",
                "metadata": {
                    "attachments": [{"original_filename": "doc.pdf"}],
                    "attachmentSummaries": [{"filename": "doc.pdf", "parsed": True}],
                },
            },
        ],
        "expect_ambiguity": True,
    },
]
