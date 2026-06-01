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
